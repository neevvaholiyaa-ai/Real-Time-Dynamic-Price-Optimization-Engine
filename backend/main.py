"""
FastAPI Backend for Real-Time Dynamic Price Optimization Engine.
Provides complete multi-user dynamic pricing platform APIs with JWT cookie authentication,
product CRUD, ML optimization inference, guardrail management, and analytics.
"""
import os
import sys
import uuid
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import get_model_bundle
from src.config import CATEGORY_CONFIG
from backend.database import fetch_one, fetch_all, execute_query, init_db
from backend.auth import (
    get_current_user,
    register_user,
    authenticate_user,
    create_access_token,
    COOKIE_NAME,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend.engine import (
    analyze_product_pricing,
    CATEGORY_ELASTICITIES
)
from backend.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    AnalysisResponse,
    SalesRecordCreateRequest,
    SalesRecordResponse,
    PricingHistoryResponse,
    UserSettingsRequest,
    UserSettingsResponse,
    DashboardOverviewResponse,
    DashboardQueueItem,
    DashboardAnalyticsResponse,
    PricePredictionRequest,
    PricePredictionResponse
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load model bundle and verify database at server startup."""
    try:
        init_db()
        bundle = get_model_bundle()
        feature_count = len(bundle.get("feature_columns", []))
        print(f"[FastAPI Startup] Model loaded successfully ({feature_count} features). Database ready.")
    except Exception as e:
        print(f"[FastAPI Startup Warning] {e}")
    yield

# Initialize FastAPI App
app = FastAPI(
    title="Real-Time Dynamic Price Optimization Engine",
    description="User-first Dynamic Pricing Intelligence & Margin Optimization Platform.",
    version="3.0.0",
    lifespan=lifespan
)

# CORS Configuration
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# 1. AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/auth/register", response_model=UserResponse, tags=["Authentication"])
def register(req: UserRegisterRequest, response: Response):
    """Registers a new user and sets a secure HttpOnly session cookie."""
    try:
        user = register_user(
            email=req.email,
            password=req.password,
            display_name=req.display_name or req.email.split("@")[0]
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = create_access_token({"sub": user["user_id"]})
    # Set HttpOnly session cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=os.environ.get("ENV", "development") == "production",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return user

@app.post("/api/auth/login", response_model=UserResponse, tags=["Authentication"])
def login(req: UserLoginRequest, response: Response):
    """Authenticates credentials and sets a secure HttpOnly session cookie."""
    user = authenticate_user(email=req.email, password=req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({"sub": user["user_id"]})
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=os.environ.get("ENV", "development") == "production",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    return user

@app.post("/api/auth/logout", tags=["Authentication"])
def logout(response: Response):
    """Clears the authentication session cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"status": "logged_out", "message": "Session terminated successfully."}

@app.get("/api/auth/me", response_model=UserResponse, tags=["Authentication"])
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns profile information for the authenticated user."""
    return current_user

# =============================================================================
# 2. PRODUCT CRUD ENDPOINTS (Strictly User-Scoped)
# =============================================================================

@app.post("/api/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(req: ProductCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Creates a new product owned by the authenticated user."""
    if req.cost_price > req.mrp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cost price (₹{req.cost_price:.2f}) cannot exceed MRP (₹{req.mrp:.2f})."
        )

    product_id = str(uuid.uuid4())
    user_id = current_user["user_id"]

    execute_query(
        """
        INSERT INTO products (
            product_id, user_id, product_name, category, brand, sku, location,
            cost_price, current_price, mrp, minimum_price, maximum_price, target_margin,
            stock_quantity, average_daily_sales, reorder_threshold,
            competitor_price, competitor_name, business_goal
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id, user_id, req.product_name, req.category, req.brand, req.sku, req.location,
            req.cost_price, req.current_price, req.mrp, req.minimum_price, req.maximum_price, req.target_margin,
            req.stock_quantity, req.average_daily_sales, req.reorder_threshold,
            req.competitor_price, req.competitor_name, req.business_goal
        )
    )

    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    return product

@app.get("/api/products", response_model=List[ProductResponse], tags=["Products"])
def list_products(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists all products belonging exclusively to the authenticated user."""
    products = fetch_all(
        "SELECT * FROM products WHERE user_id = ? ORDER BY created_at DESC",
        (current_user["user_id"],)
    )
    return products

@app.get("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def get_product(product_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves a single product with strict user ownership verification."""
    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    if not product or product["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product

@app.put("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
def update_product(product_id: str, req: ProductUpdateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Updates an existing product with strict user ownership verification."""
    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    if not product or product["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    update_dict = req.model_dump(exclude_unset=True)
    if not update_dict:
        return product

    # Validate cost vs MRP if updated
    new_cost = update_dict.get("cost_price", product["cost_price"])
    new_mrp = update_dict.get("mrp", product["mrp"])
    if new_cost > new_mrp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cost price (₹{new_cost:.2f}) cannot exceed MRP (₹{new_mrp:.2f})."
        )

    set_clauses = [f"{k} = ?" for k in update_dict.keys()]
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    values = list(update_dict.values()) + [product_id, current_user["user_id"]]

    query = f"UPDATE products SET {', '.join(set_clauses)} WHERE product_id = ? AND user_id = ?"
    execute_query(query, tuple(values))

    updated = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    return updated

@app.delete("/api/products/{product_id}", tags=["Products"])
def delete_product(product_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Deletes a product and cascades associated analyses."""
    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    if not product or product["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    execute_query("DELETE FROM products WHERE product_id = ? AND user_id = ?", (product_id, current_user["user_id"]))
    return {"status": "deleted", "product_id": product_id}

# =============================================================================
# 3. ANALYSIS & PRICING OPTIMIZATION ENDPOINTS
# =============================================================================

@app.post("/api/products/{product_id}/analyze", response_model=AnalysisResponse, tags=["Analysis"])
def analyze_product(product_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Runs LightGBM dynamic price analysis on a saved product, applies guardrails,
    classifies confidence, tracks feature provenance, and saves the analysis.
    """
    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    if not product or product["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    settings = fetch_one("SELECT * FROM user_settings WHERE user_id = ?", (current_user["user_id"],))

    # Run complete analysis engine
    analysis_data = analyze_product_pricing(product, settings)
    analysis_id = str(uuid.uuid4())
    user_id = current_user["user_id"]

    execute_query(
        """
        INSERT INTO pricing_analyses (
            analysis_id, user_id, product_id,
            input_cost_price, input_current_price, input_mrp, input_competitor_price,
            input_stock_quantity, input_daily_orders,
            recommended_price, price_change, price_change_pct, recommendation,
            margin_current_pct, margin_recommended_pct, margin_lift_pct,
            competitor_gap_pct, stock_runway_days,
            expected_demand, expected_revenue_30d, expected_profit_30d,
            confidence_level, confidence_details,
            guardrail_applied, guardrail_details,
            min_allowed_price, max_allowed_price,
            insights, economic_drivers, feature_provenance, status
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending'
        )
        """,
        (
            analysis_id, user_id, product_id,
            product["cost_price"], product["current_price"], product["mrp"], product["competitor_price"],
            product["stock_quantity"], product["average_daily_sales"],
            analysis_data["recommended_price"], analysis_data["price_change"], analysis_data["price_change_pct"],
            analysis_data["recommendation"],
            analysis_data["margin_current_pct"], analysis_data["margin_recommended_pct"], analysis_data["margin_lift_pct"],
            analysis_data["competitor_gap_pct"], analysis_data["stock_runway_days"],
            analysis_data["expected_demand"], analysis_data["expected_revenue_30d"], analysis_data["expected_profit_30d"],
            analysis_data["confidence_level"], json.dumps(analysis_data["confidence_details"]),
            1 if analysis_data["guardrail_applied"] else 0, json.dumps(analysis_data["guardrail_details"]),
            analysis_data["min_allowed_price"], analysis_data["max_allowed_price"],
            json.dumps(analysis_data["insights"]), json.dumps(analysis_data["economic_drivers"]),
            json.dumps(analysis_data["feature_provenance"])
        )
    )

    created = fetch_one("SELECT * FROM pricing_analyses WHERE analysis_id = ?", (analysis_id,))
    # Parse JSON fields for response
    serialized = _serialize_analysis(created, product)
    serialized["topology_curve"] = analysis_data.get("topology_curve", [])
    return serialized

@app.get("/api/analyses", response_model=List[AnalysisResponse], tags=["Analysis"])
def list_analyses(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists all analyses run by the authenticated user."""
    analyses = fetch_all(
        """
        SELECT a.*, p.product_name, p.category
        FROM pricing_analyses a
        JOIN products p ON a.product_id = p.product_id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
        """,
        (current_user["user_id"],)
    )
    return [_serialize_analysis(a, a) for a in analyses]

@app.get("/api/products/{product_id}/analyses", response_model=List[AnalysisResponse], tags=["Analysis"])
def get_product_analyses(product_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists analyses for a specific product owned by the user."""
    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    if not product or product["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    analyses = fetch_all(
        "SELECT * FROM pricing_analyses WHERE product_id = ? AND user_id = ? ORDER BY created_at DESC",
        (product_id, current_user["user_id"])
    )
    return [_serialize_analysis(a, product) for a in analyses]

@app.put("/api/analyses/{analysis_id}/apply", tags=["Analysis"])
def apply_analysis_recommendation(analysis_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Applies the AI recommended price to the user's product:
    1. Validates user ownership
    2. Re-validates against current guardrails
    3. Updates product current_price
    4. Records entry in pricing_history
    5. Marks analysis as 'applied'
    """
    analysis = fetch_one("SELECT * FROM pricing_analyses WHERE analysis_id = ?", (analysis_id,))
    if not analysis or analysis["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")

    if analysis["status"] == "applied":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recommendation has already been applied.")

    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (analysis["product_id"],))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target product no longer exists.")

    settings = fetch_one("SELECT * FROM user_settings WHERE user_id = ?", (current_user["user_id"],))
    old_price = product["current_price"]
    new_price = analysis["recommended_price"]

    # Re-verify guardrails
    if new_price < product["cost_price"] and settings.get("never_below_cost", 1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot apply: Recommended price (₹{new_price:.2f}) violates Never-Below-Cost guardrail."
        )

    # 1. Update Product Price
    execute_query(
        "UPDATE products SET current_price = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ? AND user_id = ?",
        (new_price, product["product_id"], current_user["user_id"])
    )

    # 2. Record Pricing History
    history_id = str(uuid.uuid4())
    change_pct = ((new_price - old_price) / old_price) * 100.0 if old_price > 0 else 0.0
    execute_query(
        """
        INSERT INTO pricing_history (history_id, user_id, product_id, analysis_id, old_price, new_price, change_pct, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (history_id, current_user["user_id"], product["product_id"], analysis_id, old_price, new_price, change_pct, "Applied AI Dynamic Pricing Recommendation")
    )

    # 3. Mark Analysis Applied
    execute_query(
        "UPDATE pricing_analyses SET status = 'applied', applied_at = CURRENT_TIMESTAMP WHERE analysis_id = ?",
        (analysis_id,)
    )

    return {
        "status": "applied",
        "product_id": product["product_id"],
        "old_price": old_price,
        "new_price": new_price,
        "change_pct": round(change_pct, 2)
    }

@app.put("/api/analyses/{analysis_id}/dismiss", tags=["Analysis"])
def dismiss_analysis(analysis_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Marks an analysis as dismissed."""
    analysis = fetch_one("SELECT * FROM pricing_analyses WHERE analysis_id = ?", (analysis_id,))
    if not analysis or analysis["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")

    execute_query("UPDATE pricing_analyses SET status = 'dismissed' WHERE analysis_id = ?", (analysis_id,))
    return {"status": "dismissed", "analysis_id": analysis_id}

# =============================================================================
# 4. SALES HISTORY ENDPOINTS (Actual Historical Data)
# =============================================================================

@app.post("/api/products/{product_id}/sales", response_model=SalesRecordResponse, status_code=status.HTTP_201_CREATED, tags=["Sales"])
def add_sales_record(product_id: str, req: SalesRecordCreateRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Adds an actual historical sales record for a user's product."""
    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    if not product or product["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    revenue = req.revenue if req.revenue is not None else (req.units_sold * req.selling_price)
    cost = req.cost if req.cost is not None else (req.units_sold * product["cost_price"])
    profit = req.profit if req.profit is not None else (revenue - cost)
    record_id = str(uuid.uuid4())

    execute_query(
        """
        INSERT INTO sales_history (record_id, user_id, product_id, period_date, units_sold, selling_price, revenue, cost, profit, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (record_id, current_user["user_id"], product_id, req.period_date, req.units_sold, req.selling_price, revenue, cost, profit, req.source)
    )

    created = fetch_one("SELECT * FROM sales_history WHERE record_id = ?", (record_id,))
    return created

@app.get("/api/products/{product_id}/sales", response_model=List[SalesRecordResponse], tags=["Sales"])
def get_product_sales(product_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves actual historical sales records for a product."""
    product = fetch_one("SELECT * FROM products WHERE product_id = ?", (product_id,))
    if not product or product["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    records = fetch_all(
        "SELECT * FROM sales_history WHERE product_id = ? AND user_id = ? ORDER BY period_date ASC",
        (product_id, current_user["user_id"])
    )
    return records

# =============================================================================
# 5. DASHBOARD & ANALYTICS ENDPOINTS (Strictly User-Calculated)
# =============================================================================

@app.get("/api/dashboard/overview", response_model=DashboardOverviewResponse, tags=["Dashboard"])
def get_dashboard_overview(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Computes dashboard overview metrics strictly from the authenticated user's data.
    Returns None / informative empty states if no data has been added yet.
    """
    user_id = current_user["user_id"]

    # 1. Total Distinct Products Analyzed
    count_row = fetch_one("SELECT COUNT(DISTINCT product_id) as cnt FROM pricing_analyses WHERE user_id = ?", (user_id,))
    analyzed_count = count_row["cnt"] if count_row else 0

    # 2. Avg Optimized Margin Lift
    lift_row = fetch_one("SELECT AVG(margin_lift_pct) as avg_lift FROM pricing_analyses WHERE user_id = ? AND status != 'dismissed'", (user_id,))
    avg_lift = round(lift_row["avg_lift"], 1) if (lift_row and lift_row["avg_lift"] is not None) else None

    # 3. Price Elasticity Index across user's product categories
    categories = fetch_all(
        "SELECT DISTINCT p.category FROM pricing_analyses a JOIN products p ON a.product_id = p.product_id WHERE a.user_id = ?",
        (user_id,)
    )
    if categories:
        elasticities = [CATEGORY_ELASTICITIES.get(c["category"], -1.4) for c in categories if c.get("category")]
        avg_elasticity = round(sum(elasticities) / len(elasticities), 2) if elasticities else None
    else:
        avg_elasticity = None

    # 4. Competitor Price Gap
    gap_row = fetch_one("SELECT AVG(competitor_gap_pct) as avg_gap FROM pricing_analyses WHERE user_id = ? AND competitor_gap_pct IS NOT NULL", (user_id,))
    if gap_row and gap_row["avg_gap"] is not None:
        avg_gap = round(gap_row["avg_gap"], 1)
        comp_label = f"{avg_gap:+.1f}% vs competitor benchmark"
    else:
        avg_gap = None
        comp_label = "No competitor data provided"

    # 5. Stock Runway Velocity
    runway_row = fetch_one("SELECT AVG(stock_runway_days) as avg_runway FROM pricing_analyses WHERE user_id = ? AND stock_runway_days IS NOT NULL", (user_id,))
    if runway_row and runway_row["avg_runway"] is not None:
        avg_runway = round(runway_row["avg_runway"], 1)
        stock_label = f"{avg_runway:.0f} Days Runway"
    else:
        avg_runway = None
        stock_label = "No inventory data provided"

    # 6. Pending Actions Count
    pending_row = fetch_one("SELECT COUNT(*) as cnt FROM pricing_analyses WHERE user_id = ? AND status = 'pending'", (user_id,))
    pending_count = pending_row["cnt"] if pending_row else 0

    # 7. Projected 30-Day Profit & Revenue Opportunity
    proj_row = fetch_one(
        """
        SELECT
            SUM(expected_profit_30d) as total_profit,
            SUM(expected_revenue_30d) as total_revenue
        FROM pricing_analyses
        WHERE user_id = ? AND status = 'pending'
        """,
        (user_id,)
    )
    proj_profit = round(proj_row["total_profit"], 2) if (proj_row and proj_row["total_profit"] is not None) else None
    proj_revenue = round(proj_row["total_revenue"], 2) if (proj_row and proj_row["total_revenue"] is not None) else None

    # 8. Dynamic Pricing Signals from User Analyses
    analyses = fetch_all(
        "SELECT a.*, p.product_name FROM pricing_analyses a JOIN products p ON a.product_id = p.product_id WHERE a.user_id = ? ORDER BY a.created_at DESC LIMIT 10",
        (user_id,)
    )
    signals = []
    for a in analyses:
        if a["margin_lift_pct"] and a["margin_lift_pct"] > 3.0:
            signals.append({
                "icon": "trending_up",
                "icon_class": "signal-icon-emerald",
                "title": f"Margin Headroom: {a['product_name']}",
                "desc": f"+{a['margin_lift_pct']:.1f}% margin lift available at recommended price of ₹{a['recommended_price']:,.2f}.",
                "meta": f"Confidence: {a['confidence_level'].upper()}"
            })
        if a["stock_runway_days"] and a["stock_runway_days"] < 5.0:
            signals.append({
                "icon": "warning",
                "icon_class": "signal-icon-amber",
                "title": f"Low Stock Runway: {a['product_name']}",
                "desc": f"Only {a['stock_runway_days']:.1f} days remaining. Scarcity premium active to prevent stockout.",
                "meta": "Scarcity Yield"
            })
        if a["competitor_gap_pct"] and a["competitor_gap_pct"] < -5.0:
            signals.append({
                "icon": "storefront",
                "icon_class": "signal-icon-blue",
                "title": f"Value Advantage: {a['product_name']}",
                "desc": f"Priced {abs(a['competitor_gap_pct']):.1f}% below market competitor. Room for margin expansion.",
                "meta": "Market Advantage"
            })

    if not signals and analyzed_count == 0:
        signals.append({
            "icon": "info",
            "icon_class": "signal-icon-blue",
            "title": "Welcome to AuraPrice",
            "desc": "Add your first product to generate AI pricing recommendations and live dynamic signals.",
            "meta": "Ready to Start"
        })

    return {
        "products_analyzed_count": analyzed_count,
        "avg_margin_lift_pct": avg_lift,
        "price_elasticity_index": avg_elasticity,
        "competitor_gap_avg_pct": avg_gap,
        "competitor_status_label": comp_label,
        "stock_runway_avg_days": avg_runway,
        "stock_status_label": stock_label,
        "pending_actions_count": pending_count,
        "projected_profit_opportunity_30d": proj_profit,
        "projected_revenue_opportunity_30d": proj_revenue,
        "signals": signals
    }

@app.get("/api/dashboard/queue", response_model=List[DashboardQueueItem], tags=["Dashboard"])
def get_dashboard_queue(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns the pending reprice action queue exclusively for the authenticated user's products.
    """
    user_id = current_user["user_id"]
    rows = fetch_all(
        """
        SELECT
            a.analysis_id,
            a.product_id,
            p.product_name,
            COALESCE(p.category, 'General') as category,
            p.cost_price,
            p.current_price,
            a.recommended_price,
            a.price_change,
            a.price_change_pct,
            p.competitor_price,
            a.competitor_gap_pct,
            a.stock_runway_days,
            a.confidence_level,
            a.margin_lift_pct,
            a.expected_profit_30d as projected_profit_lift_30d,
            a.status,
            a.created_at
        FROM pricing_analyses a
        JOIN products p ON a.product_id = p.product_id
        WHERE a.user_id = ? AND a.status = 'pending'
        ORDER BY a.created_at DESC
        """,
        (user_id,)
    )
    return [dict(r) for r in rows]

@app.get("/api/dashboard/analytics", response_model=DashboardAnalyticsResponse, tags=["Dashboard"])
def get_dashboard_analytics(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns Revenue & Margin Analytics strictly computed from the user's data.
    Strictly distinguishes Actual Historical data from Model-Estimated Projections.
    """
    user_id = current_user["user_id"]

    prod_count = fetch_one("SELECT COUNT(*) as cnt FROM products WHERE user_id = ?", (user_id,))
    total_products = prod_count["cnt"] if prod_count else 0

    analysis_count = fetch_one("SELECT COUNT(*) as cnt FROM pricing_analyses WHERE user_id = ?", (user_id,))
    total_analyses = analysis_count["cnt"] if analysis_count else 0

    # 1. Actual Sales History (if user provided)
    sales_agg = fetch_one(
        "SELECT SUM(revenue) as tot_rev, SUM(profit) as tot_prof, COUNT(*) as cnt FROM sales_history WHERE user_id = ?",
        (user_id,)
    )
    has_actual = (sales_agg and sales_agg["cnt"] > 0)
    actual_rev = round(sales_agg["tot_rev"], 2) if (has_actual and sales_agg["tot_rev"] is not None) else None
    actual_prof = round(sales_agg["tot_prof"], 2) if (has_actual and sales_agg["tot_prof"] is not None) else None

    # Actual Trajectory (period breakdown)
    trajectory = []
    if has_actual:
        traj_rows = fetch_all(
            "SELECT period_date, SUM(revenue) as rev, SUM(profit) as prof, SUM(units_sold) as units FROM sales_history WHERE user_id = ? GROUP BY period_date ORDER BY period_date ASC",
            (user_id,)
        )
        trajectory = [
            {
                "period": r["period_date"],
                "actual_revenue": round(r["rev"], 2),
                "actual_profit": round(r["prof"], 2),
                "units": r["units"],
                "is_actual": True
            }
            for r in traj_rows
        ]

    # 2. Projected 30-Day Projections from latest analyses
    proj_agg = fetch_one(
        """
        SELECT
            SUM(expected_revenue_30d) as proj_rev,
            SUM(expected_profit_30d) as proj_prof,
            AVG(margin_lift_pct) as avg_lift
        FROM pricing_analyses
        WHERE user_id = ? AND status != 'dismissed'
        """,
        (user_id,)
    )
    proj_rev = round(proj_agg["proj_rev"], 2) if (proj_agg and proj_agg["proj_rev"] is not None) else None
    proj_prof = round(proj_agg["proj_prof"], 2) if (proj_agg and proj_agg["proj_prof"] is not None) else None

    # Incremental profit lift
    proj_inc_lift = None
    if proj_prof is not None and proj_agg and proj_agg["avg_lift"] is not None:
        proj_inc_lift = round(proj_prof * (proj_agg["avg_lift"] / 100.0), 2)

    # 3. Category Breakdown (from user's products only)
    cat_rows = fetch_all(
        """
        SELECT
            COALESCE(p.category, 'General') as category,
            COUNT(DISTINCT p.product_id) as sku_count,
            AVG((p.current_price - p.cost_price) / p.current_price * 100.0) as avg_margin
        FROM products p
        WHERE p.user_id = ?
        GROUP BY p.category
        """,
        (user_id,)
    )
    cat_breakdown = [
        {
            "category": r["category"],
            "sku_count": r["sku_count"],
            "avg_margin_pct": round(r["avg_margin"], 1) if r["avg_margin"] is not None else 0.0
        }
        for r in cat_rows
    ]

    return {
        "total_products_count": total_products,
        "total_analyzed_count": total_analyses,
        "has_actual_sales_data": has_actual,
        "actual_historical_revenue": actual_rev,
        "actual_historical_profit": actual_prof,
        "projected_total_revenue_30d": proj_rev,
        "projected_total_profit_30d": proj_prof,
        "projected_incremental_profit_lift_30d": proj_inc_lift,
        "category_margin_breakdown": cat_breakdown,
        "sales_trajectory": trajectory
    }

# =============================================================================
# 6. USER SETTINGS & GUARDRAILS ENDPOINTS
# =============================================================================

@app.get("/api/settings", response_model=UserSettingsResponse, tags=["Settings"])
def get_user_settings(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves guardrail and currency settings for the authenticated user."""
    settings = fetch_one("SELECT * FROM user_settings WHERE user_id = ?", (current_user["user_id"],))
    if not settings:
        # Create default settings if not exists
        execute_query(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (current_user["user_id"],)
        )
        settings = fetch_one("SELECT * FROM user_settings WHERE user_id = ?", (current_user["user_id"],))

    return {
        "user_id": settings["user_id"],
        "margin_floor_pct": settings["margin_floor_pct"],
        "corridor_min_pct": settings["corridor_min_pct"],
        "corridor_max_pct": settings["corridor_max_pct"],
        "max_discount_pct": settings["max_discount_pct"],
        "max_price_change_pct": settings["max_price_change_pct"],
        "never_below_cost": bool(settings["never_below_cost"]),
        "never_above_mrp": bool(settings["never_above_mrp"]),
        "custom_price_floor": settings["custom_price_floor"],
        "custom_price_ceiling": settings["custom_price_ceiling"],
        "currency": settings["currency"] or "INR",
        "store_name": settings["store_name"]
    }

@app.put("/api/settings", response_model=UserSettingsResponse, tags=["Settings"])
def update_user_settings(req: UserSettingsRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Updates guardrails and preferences for the authenticated user."""
    user_id = current_user["user_id"]
    execute_query(
        """
        UPDATE user_settings SET
            margin_floor_pct = ?,
            corridor_min_pct = ?,
            corridor_max_pct = ?,
            max_discount_pct = ?,
            max_price_change_pct = ?,
            never_below_cost = ?,
            never_above_mrp = ?,
            custom_price_floor = ?,
            custom_price_ceiling = ?,
            currency = ?,
            store_name = ?
        WHERE user_id = ?
        """,
        (
            req.margin_floor_pct, req.corridor_min_pct, req.corridor_max_pct,
            req.max_discount_pct, req.max_price_change_pct,
            1 if req.never_below_cost else 0, 1 if req.never_above_mrp else 0,
            req.custom_price_floor, req.custom_price_ceiling,
            req.currency, req.store_name,
            user_id
        )
    )
    return get_user_settings(current_user)

# =============================================================================
# 7. STATELESS SIMULATION ENDPOINT (What-If Sandbox — Never saves to DB)
# =============================================================================

@app.post("/predict", response_model=PricePredictionResponse, tags=["Simulation"])
def simulate_price_prediction(req: PricePredictionRequest):
    """
    Stateless LightGBM simulation endpoint.
    Executes what-if scenarios without modifying or persisting anything to the database.
    """
    if req.cost_price > req.mrp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cost price (₹{req.cost_price:.2f}) cannot exceed MRP (₹{req.mrp:.2f})."
        )

    product_dict = req.model_dump()
    if not product_dict.get("city") and product_dict.get("location"):
        product_dict["city"] = product_dict["location"]
    if not product_dict.get("location") and product_dict.get("city"):
        product_dict["location"] = product_dict["city"]

    analysis_data = analyze_product_pricing(product_dict)

    return {
        "product_id": req.product_id or "PROD-SIM-001",
        "product_name": req.product_name or "Target SKU",
        "category": req.category,
        "city": product_dict.get("city") or "Ahmedabad",
        "current_price": req.current_price,
        "recommended_price": analysis_data["recommended_price"],
        "price_change": analysis_data["price_change"],
        "price_change_percent": analysis_data["price_change_pct"],
        "recommendation": analysis_data["recommendation"],
        "guardrail_applied": analysis_data["guardrail_applied"],
        "guardrail_details": analysis_data["guardrail_details"],
        "min_allowed_price": analysis_data["min_allowed_price"],
        "max_allowed_price": analysis_data["max_allowed_price"],
        "confidence_level": analysis_data["confidence_level"],
        "confidence_details": analysis_data["confidence_details"],
        "insights": analysis_data["insights"],
        "economic_drivers": analysis_data["economic_drivers"],
        "feature_provenance": analysis_data["feature_provenance"],
        "topology_curve": analysis_data["topology_curve"]
    }

# =============================================================================
# 8. REFERENCE & UTILITY ENDPOINTS
# =============================================================================

@app.get("/api/categories", tags=["Reference"])
def get_categories():
    """Returns supported product categories and single-source-of-truth baseline settings."""
    return [
        {
            "category": cat_name,
            "seeded_elasticity": cfg["seeded_elasticity"],
            "avg_margin_pct": cfg["avg_margin_pct"],
            "marketplace_fee_pct": cfg["marketplace_fee_pct"]
        }
        for cat_name, cfg in CATEGORY_CONFIG.items()
    ]

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint returning system status."""
    bundle = get_model_bundle()
    model_ready = bundle is not None and "model" in bundle
    return {
        "status": "healthy" if model_ready else "degraded",
        "model_loaded": model_ready,
        "supported_categories": list(CATEGORY_CONFIG.keys()),
        "version": "3.0.0"
    }

# -----------------------------------------------------------------------------
# Internal Serialization Helper
# -----------------------------------------------------------------------------
def _serialize_analysis(a: Dict[str, Any], p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "analysis_id": a["analysis_id"],
        "user_id": a["user_id"],
        "product_id": a["product_id"],
        "product_name": p.get("product_name"),
        "category": p.get("category"),
        "input_cost_price": a["input_cost_price"],
        "input_current_price": a["input_current_price"],
        "input_mrp": a["input_mrp"],
        "input_competitor_price": a["input_competitor_price"],
        "input_stock_quantity": a["input_stock_quantity"],
        "input_daily_orders": a["input_daily_orders"],
        "recommended_price": a["recommended_price"],
        "price_change": a["price_change"],
        "price_change_pct": a["price_change_pct"],
        "recommendation": a["recommendation"],
        "margin_current_pct": a["margin_current_pct"],
        "margin_recommended_pct": a["margin_recommended_pct"],
        "margin_lift_pct": a["margin_lift_pct"],
        "competitor_gap_pct": a["competitor_gap_pct"],
        "stock_runway_days": a["stock_runway_days"],
        "expected_demand": a["expected_demand"],
        "expected_revenue_30d": a["expected_revenue_30d"],
        "expected_profit_30d": a["expected_profit_30d"],
        "confidence_level": a["confidence_level"] or "medium",
        "confidence_details": json.loads(a["confidence_details"]) if a.get("confidence_details") else [],
        "guardrail_applied": bool(a["guardrail_applied"]),
        "guardrail_details": json.loads(a["guardrail_details"]) if a.get("guardrail_details") else [],
        "min_allowed_price": a["min_allowed_price"],
        "max_allowed_price": a["max_allowed_price"],
        "insights": json.loads(a["insights"]) if a.get("insights") else [],
        "economic_drivers": json.loads(a["economic_drivers"]) if a.get("economic_drivers") else [],
        "feature_provenance": json.loads(a["feature_provenance"]) if a.get("feature_provenance") else {},
        "topology_curve": a.get("topology_curve") or [],
        "status": a["status"],
        "applied_at": str(a["applied_at"]) if a.get("applied_at") else None,
        "created_at": str(a["created_at"]) if a.get("created_at") else None
    }

# =============================================================================
# 9. STATIC FILES & SPA SERVING
# =============================================================================

FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/", tags=["Frontend"])
@app.get("/{full_path:path}", tags=["Frontend"])
def serve_spa(full_path: str = ""):
    """Serves static assets if found, or the single-page application index.html."""
    if full_path:
        requested_file = FRONTEND_DIR / full_path
        if requested_file.exists() and requested_file.is_file():
            return FileResponse(str(requested_file))
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"message": "Frontend index.html not found"}, status_code=404)
