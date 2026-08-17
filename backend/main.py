"""
FastAPI Backend for Real-Time Dynamic Price Optimization Engine.
Serves dynamic price prediction endpoints and mounts the web application dashboard.
Production-ready for Render (Backend) and Vercel (Frontend).
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import predict_optimal_price, get_model_bundle
from src.product_catalog import build_product_catalog
from backend.schemas import PricePredictionRequest, PricePredictionResponse

# Cached product catalog
_MASTER_CATALOG: List[Dict[str, Any]] = []

def get_master_catalog() -> List[Dict[str, Any]]:
    global _MASTER_CATALOG
    if not _MASTER_CATALOG:
        try:
            _MASTER_CATALOG = build_product_catalog()
        except Exception as e:
            print(f"[Catalog Load Warning] {e}")
    return _MASTER_CATALOG

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load model bundle and product catalog into memory at server startup."""
    try:
        bundle = get_model_bundle()
        feature_count = len(bundle.get("feature_columns", []))
        print(f"[FastAPI Startup] Model loaded successfully ({feature_count} features).")
        catalog = get_master_catalog()
        print(f"[FastAPI Startup] Master catalog loaded ({len(catalog)} SKUs across 8 categories).")
    except Exception as e:
        print(f"[FastAPI Startup Error] {e}")
    yield

# Initialize FastAPI App
app = FastAPI(
    title="Real-Time Dynamic Price Optimization Engine",
    description="Dynamic pricing intelligence and gross margin optimization microservice for Ahmedabad and Surat.",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS (Supports localhost, Vercel frontend domains, or custom origins)
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint returning system status and model readiness.
    """
    try:
        bundle = get_model_bundle()
        model_ready = bundle is not None and "model" in bundle
    except Exception:
        model_ready = False

    return {
        "status": "healthy" if model_ready else "degraded",
        "model_loaded": model_ready,
        "supported_cities": ["Ahmedabad", "Surat"],
        "supported_categories": [
            "Electronics", "Fashion", "Footwear", "Grocery",
            "Home & Kitchen", "Mobile Accessories", "Personal Care", "Sports & Fitness"
        ],
        "total_skus": len(get_master_catalog()),
        "version": "2.0.0"
    }

@app.get("/api/settings", tags=["System"])
def get_system_settings():
    """
    Returns active pricing rules, guardrails, and model telemetry metadata.
    """
    return {
        "supported_cities": ["Ahmedabad", "Surat"],
        "margin_floor_pct": 5.5,
        "competitor_corridor_min_pct": -15.0,
        "competitor_corridor_max_pct": 10.0,
        "max_discount_from_mrp_pct": 40.0,
        "model_architecture": "LightGBM Gradient Boosted Decision Trees",
        "feature_count": 57,
        "training_timeframe": "Multi-year historical Gujarat retail transactions",
        "auto_pilot_enabled": False
    }

@app.get("/api/categories", tags=["Catalog"])
def get_categories():
    """
    Returns the list of 8 retail categories supported by the engine.
    """
    catalog = get_master_catalog()
    cats = sorted(list(set(p.get("Category", "") for p in catalog if p.get("Category"))))
    if not cats:
        cats = [
            "Electronics", "Fashion", "Footwear", "Grocery",
            "Home & Kitchen", "Mobile Accessories", "Personal Care", "Sports & Fitness"
        ]
    return cats

@app.get("/api/catalog", tags=["Catalog"])
def get_full_catalog(category: Optional[str] = None):
    """
    Returns the master dataset of 130 SKUs, optionally filtered by category.
    """
    catalog = get_master_catalog()
    if category and category.lower() != "all":
        return [p for p in catalog if p.get("Category", "").lower() == category.lower()]
    return catalog

@app.post("/predict", response_model=PricePredictionResponse, tags=["Pricing"])
def predict_price(request: PricePredictionRequest):
    """
    Real-Time Dynamic Price Optimization Endpoint.
    """
    # Enforce strictly Ahmedabad & Surat
    if request.city not in ["Ahmedabad", "Surat"]:
        request.city = "Ahmedabad"

    try:
        input_data = request.model_dump()
        result = predict_optimal_price(input_data)
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference execution failed: {str(exc)}"
        )

@app.get("/api/catalog-samples", tags=["Catalog"])
def get_catalog_samples():
    """
    Provides curated product presets representing diverse e-commerce retail scenarios in Ahmedabad & Surat.
    """
    return [
        {
            "id": "festive-kurta",
            "name": "Festive Kurta",
            "subtitle": "Diwali demand spike",
            "icon": "celebration",
            "product_id": "PROD-FASH-001",
            "product_name": "Handcrafted Bandhani Festive Kurta",
            "category": "Fashion",
            "city": "Ahmedabad",
            "cost_price": 650.0,
            "current_price": 1299.0,
            "mrp": 1999.0,
            "competitor_avg_price": 1350.0,
            "stock_level": 90,
            "orders": 48,
            "days_until_next_festival": 5,
            "weather_type": "Clear",
            "competitor_stock_status": "Low_Stock"
        },
        {
            "id": "basmati-rice",
            "name": "Basmati Rice 5kg",
            "subtitle": "Steady grocery item",
            "icon": "inventory_2",
            "product_id": "PROD-GROC-002",
            "product_name": "Royal Premium Basmati Rice 5kg",
            "category": "Grocery",
            "city": "Surat",
            "cost_price": 420.0,
            "current_price": 640.0,
            "mrp": 750.0,
            "competitor_avg_price": 650.0,
            "stock_level": 450,
            "orders": 35,
            "days_until_next_festival": 60,
            "weather_type": "Rainy",
            "competitor_stock_status": "In_Stock"
        },
        {
            "id": "wireless-earbuds",
            "name": "Wireless Earbuds ANC",
            "subtitle": "High competition audio",
            "icon": "headphones",
            "product_id": "PROD-ELEC-003",
            "product_name": "True Wireless Noise Cancelling Earbuds",
            "category": "Electronics",
            "city": "Ahmedabad",
            "cost_price": 1800.0,
            "current_price": 2999.0,
            "mrp": 3999.0,
            "competitor_avg_price": 2950.0,
            "stock_level": 80,
            "orders": 40,
            "days_until_next_festival": 25,
            "weather_type": "Clear",
            "competitor_stock_status": "In_Stock"
        },
        {
            "id": "smart-watch",
            "name": "Smart Fitness Watch",
            "subtitle": "Wearables category",
            "icon": "watch",
            "product_id": "PROD-ELEC-004",
            "product_name": "Smart Fitness Watch 1.83 inch",
            "category": "Electronics",
            "city": "Surat",
            "cost_price": 1400.0,
            "current_price": 2899.0,
            "mrp": 3499.0,
            "competitor_avg_price": 2750.0,
            "stock_level": 600,
            "orders": 12,
            "days_until_next_festival": 45,
            "weather_type": "Clear",
            "competitor_stock_status": "In_Stock"
        },
        {
            "id": "oneplus-phone",
            "name": "OnePlus 12R 5G (Custom)",
            "subtitle": "Premium smartphone",
            "icon": "smartphone",
            "product_id": "PROD-ELEC-005",
            "product_name": "OnePlus 12R 5G 16GB/256GB",
            "category": "Electronics",
            "city": "Ahmedabad",
            "cost_price": 32000.0,
            "current_price": 39999.0,
            "mrp": 45999.0,
            "competitor_avg_price": 38990.0,
            "stock_level": 45,
            "orders": 28,
            "days_until_next_festival": 14,
            "weather_type": "Clear",
            "competitor_stock_status": "In_Stock"
        }
    ]

@app.post("/api/batch-predict", tags=["Pricing"])
def batch_predict(items: List[PricePredictionRequest]):
    """
    Batch predict optimal prices for multiple products.
    Returns a list of price recommendations.
    """
    results = []
    for item in items:
        try:
            input_dict = item.model_dump()
            result = predict_optimal_price(input_dict)
            results.append(result)
        except Exception as e:
            results.append({"product_id": item.product_id, "error": str(e)})
    return results

# =============================================================================
# Mount Static Files & Root Route
# =============================================================================

FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/", tags=["Frontend"])
def serve_dashboard():
    """Serves the main pricing dashboard web application."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({
        "message": "Dynamic Pricing API is running. Frontend index.html is being initialized."
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
