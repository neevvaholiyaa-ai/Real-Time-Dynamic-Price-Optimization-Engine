"""
Analysis & Pricing Optimization Engine.
Coordinates LightGBM model inference, feature provenance tracking,
confidence classification, multi-tier guardrail enforcement,
deterministic profit topology modeling, and rule-based economic rationale.
"""
import json
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from src.predict import (
    get_model_bundle,
    prepare_feature_vector
)
from src.config import CATEGORY_CONFIG

# Canonical 57 feature columns
FEATURE_COLUMNS = [
    'Cost_Price', 'Current_Price', 'MRP', 'Marketplace_Fee_Pct',
    'Competitor_Avg_Price', 'Competitor_Min_Price', 'Price_Gap_Pct',
    'Price_to_Competitor_Ratio', 'Competitor_Discount_Pct', 'Market_Rank',
    'Discount_Pct', 'Margin_Pct', 'Stock_Level', 'Reorder_Point',
    'Lead_Time_Days', 'Stock_Out_Risk', 'Stock_Days_Remaining',
    'Category_Code', 'City_Code', 'Weather_Code', 'Competitor_Stock_Code',
    'Day_of_Week', 'Month', 'Quarter', 'Is_Weekend', 'Is_Holiday',
    'Is_Month_End', 'Days_Until_Next_Festival', 'Days_Since_Launch',
    'Days_Since_Last_Price_Change', 'Temperature', 'Humidity', 'Rainfall',
    'Is_Extreme_Weather', 'USD_INR', 'Crude_Oil_Price_USD', 'Gold_Price',
    'Inflation_Index', 'Consumer_Confidence_Proxy', 'Fuel_Price_INR_Proxy',
    'Views', 'Clicks', 'Cart_Adds', 'Orders', 'Conversion_Rate',
    'Search_Trend_Index', 'Demand_Index', 'Return_Rate', 'Price_Lag_7',
    'Demand_Lag_7', 'Rolling_Avg_Price_30d', 'Price_Volatility_30d',
    'Demand_Momentum_7d', 'Price_Elasticity_Score', 'Festival_Impact_Score',
    'Weather_Impact_Score', 'Seasonality_Impact_Score'
]

# Static Category Elasticity Seeds from Config
CATEGORY_ELASTICITIES = {
    "Grocery": -1.0,
    "Personal Care": -1.2,
    "Home & Kitchen": -1.4,
    "Footwear": -1.6,
    "Sports & Fitness": -1.7,
    "Fashion": -1.9,
    "Mobile Accessories": -2.0,
    "Electronics": -2.2
}

def resolve_feature_provenance(product_dict: Dict[str, Any]) -> Dict[str, str]:
    """
    Classifies every one of the 57 model features into its exact provenance type
    based on whether the user provided the corresponding input.
    """
    has_comp = product_dict.get("competitor_price") is not None or product_dict.get("competitor_avg_price") is not None
    has_stock = product_dict.get("stock_quantity") is not None or product_dict.get("stock_level") is not None
    has_orders = product_dict.get("average_daily_sales") is not None or product_dict.get("orders") is not None
    has_fest = product_dict.get("days_until_next_festival") is not None
    has_reorder = product_dict.get("reorder_threshold") is not None
    has_city = product_dict.get("location") is not None or product_dict.get("city") is not None
    has_weather = product_dict.get("weather_type") is not None
    has_comp_stock = product_dict.get("competitor_stock_status") is not None

    provenance = {}
    for feat in FEATURE_COLUMNS:
        if feat in ("Cost_Price", "Current_Price", "MRP"):
            provenance[feat] = "USER_INPUT"
        elif feat in ("Discount_Pct", "Margin_Pct"):
            provenance[feat] = "DERIVED_FROM_USER_INPUT"
        elif feat == "Competitor_Avg_Price":
            provenance[feat] = "USER_INPUT" if has_comp else "MODEL_BASELINE"
        elif feat == "Stock_Level":
            provenance[feat] = "USER_INPUT" if has_stock else "MODEL_BASELINE"
        elif feat == "Orders":
            provenance[feat] = "USER_INPUT" if has_orders else "MODEL_BASELINE"
        elif feat == "Days_Until_Next_Festival":
            provenance[feat] = "USER_INPUT" if has_fest else "MODEL_BASELINE"
        elif feat == "Reorder_Point":
            provenance[feat] = "USER_INPUT" if has_reorder else "MODEL_BASELINE"
        elif feat in ("Price_Gap_Pct", "Price_to_Competitor_Ratio", "Competitor_Discount_Pct"):
            provenance[feat] = "DERIVED_FROM_USER_INPUT" if has_comp else "MODEL_ESTIMATE"
        elif feat in ("Competitor_Min_Price", "Market_Rank"):
            provenance[feat] = "MODEL_ESTIMATE"
        elif feat in ("Stock_Out_Risk", "Stock_Days_Remaining"):
            provenance[feat] = "DERIVED_FROM_USER_INPUT" if (has_stock and has_orders) else "MODEL_ESTIMATE"
        elif feat in ("Conversion_Rate", "Demand_Index", "Views", "Clicks", "Cart_Adds",
                      "Price_Lag_7", "Demand_Lag_7", "Rolling_Avg_Price_30d", "Price_Volatility_30d",
                      "Demand_Momentum_7d", "Weather_Impact_Score"):
            provenance[feat] = "MODEL_ESTIMATE"
        elif feat in ("Marketplace_Fee_Pct", "Price_Elasticity_Score", "Festival_Impact_Score", "Seasonality_Impact_Score"):
            provenance[feat] = "CATEGORY_CONFIG"
        elif feat == "Category_Code":
            provenance[feat] = "DERIVED_FROM_USER_INPUT"
        elif feat == "City_Code":
            provenance[feat] = "USER_INPUT" if has_city else "MODEL_BASELINE"
        elif feat == "Weather_Code":
            provenance[feat] = "USER_INPUT" if has_weather else "MODEL_BASELINE"
        elif feat == "Competitor_Stock_Code":
            provenance[feat] = "USER_INPUT" if has_comp_stock else "MODEL_BASELINE"
        elif feat in ("Day_of_Week", "Month", "Quarter", "Is_Weekend", "Is_Month_End"):
            provenance[feat] = "CURRENT_SYSTEM_TIME"
        else:
            provenance[feat] = "MODEL_BASELINE"

    return provenance

def classify_prediction_confidence(product_dict: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Evaluates confidence level (high, medium, low) based on the presence of actual business data.
    """
    available = []
    missing = []

    # Required
    available.append("Core pricing inputs provided (Cost, Current Price, MRP)")

    # Optional business inputs
    has_comp = product_dict.get("competitor_price") is not None or product_dict.get("competitor_avg_price") is not None
    if has_comp:
        available.append("Competitor market price provided")
    else:
        missing.append("Competitor price unavailable")

    has_stock = product_dict.get("stock_quantity") is not None or product_dict.get("stock_level") is not None
    if has_stock:
        available.append("Warehouse stock level provided")
    else:
        missing.append("Stock quantity unavailable")

    has_orders = product_dict.get("average_daily_sales") is not None or product_dict.get("orders") is not None
    if has_orders:
        available.append("Daily sales demand velocity provided")
    else:
        missing.append("Daily sales demand velocity unavailable")

    cat = product_dict.get("category")
    if cat:
        available.append(f"Product category verified ({cat})")
    else:
        missing.append("Product category unavailable")

    loc = product_dict.get("location") or product_dict.get("city")
    if loc:
        available.append(f"Store location verified ({loc})")
    else:
        missing.append("Store location unavailable")

    # Critical missing count (competitor, stock, demand)
    critical_missing = 0
    if not has_comp:
        critical_missing += 1
    if not has_stock:
        critical_missing += 1
    if not has_orders:
        critical_missing += 1

    if critical_missing == 0:
        level = "high"
    elif critical_missing == 1:
        level = "medium"
    else:
        level = "low"

    details = []
    if missing:
        details.append(f"{len(missing)} input(s) unavailable — model baselines used:")
        for m in missing:
            details.append(f"• {m}")
    if available:
        details.insert(0, f"{len(available)} input(s) actively provided")

    return level, details

def run_guardrail_checks(
    raw_price: float,
    cost_price: float,
    current_price: float,
    mrp: float,
    competitor_price: Optional[float],
    settings: Optional[Dict[str, Any]] = None
) -> Tuple[float, bool, float, float, List[Dict[str, Any]]]:
    """
    Applies comprehensive business guardrails defined by user settings or standard retail thresholds.
    """
    s = settings or {}
    margin_floor_pct = float(s.get("margin_floor_pct", 5.5))
    corridor_min_pct = float(s.get("corridor_min_pct", -25.0))
    corridor_max_pct = float(s.get("corridor_max_pct", 25.0))
    max_discount_pct = float(s.get("max_discount_pct", 40.0))
    max_price_change_pct = float(s.get("max_price_change_pct", 15.0))
    never_below_cost = bool(s.get("never_below_cost", 1))
    never_above_mrp = bool(s.get("never_above_mrp", 1))
    custom_price_floor = s.get("custom_price_floor")
    custom_price_ceiling = s.get("custom_price_ceiling")

    clipped_price = raw_price
    guardrails_fired = []

    # 1. Floor calculation
    min_allowed = cost_price * (1.0 + (margin_floor_pct / 100.0))
    if never_below_cost:
        min_allowed = max(min_allowed, cost_price)
    if custom_price_floor is not None and custom_price_floor > 0:
        min_allowed = max(min_allowed, float(custom_price_floor))

    # 2. Ceiling calculation
    max_allowed = mrp
    if custom_price_ceiling is not None and custom_price_ceiling > 0:
        max_allowed = min(max_allowed, float(custom_price_ceiling))

    # Max discount from MRP
    mrp_discount_floor = mrp * (1.0 - (max_discount_pct / 100.0))
    min_allowed = max(min_allowed, mrp_discount_floor)

    # 3. Apply Floor
    if clipped_price < min_allowed:
        orig = clipped_price
        clipped_price = min_allowed
        guardrails_fired.append({
            "rule": "Margin Floor Shield",
            "triggered": True,
            "original": round(orig, 2),
            "clipped_to": round(clipped_price, 2),
            "explanation": f"Raised price to protect minimum {margin_floor_pct:.1f}% profit margin above cost."
        })

    # 4. Apply Ceiling
    if never_above_mrp and clipped_price > max_allowed:
        orig = clipped_price
        clipped_price = max_allowed
        guardrails_fired.append({
            "rule": "MRP Ceiling Guardrail",
            "triggered": True,
            "original": round(orig, 2),
            "clipped_to": round(clipped_price, 2),
            "explanation": f"Capped price at MRP (₹{mrp:,.2f}) to prevent regulatory price gouging."
        })

    # 5. Competitor corridor (only if competitor price is user-provided)
    if competitor_price is not None and competitor_price > 0:
        c_min = competitor_price * (1.0 + (corridor_min_pct / 100.0))
        c_max = competitor_price * (1.0 + (corridor_max_pct / 100.0))
        if clipped_price < c_min:
            orig = clipped_price
            clipped_price = max(c_min, min_allowed)
            guardrails_fired.append({
                "rule": "Anti-Price War Corridor",
                "triggered": True,
                "original": round(orig, 2),
                "clipped_to": round(clipped_price, 2),
                "explanation": f"Prevented price from falling below {abs(corridor_min_pct):.0f}% of competitor benchmark."
            })
        elif clipped_price > c_max:
            orig = clipped_price
            clipped_price = min(c_max, max_allowed)
            guardrails_fired.append({
                "rule": "Competitor Premium Corridor",
                "triggered": True,
                "original": round(orig, 2),
                "clipped_to": round(clipped_price, 2),
                "explanation": f"Prevented price from exceeding {corridor_max_pct:.0f}% of competitor benchmark."
            })

    # 6. Max single-step price change
    if max_price_change_pct > 0 and current_price > 0:
        max_step_up = current_price * (1.0 + (max_price_change_pct / 100.0))
        max_step_down = current_price * (1.0 - (max_price_change_pct / 100.0))
        if clipped_price > max_step_up:
            orig = clipped_price
            clipped_price = max_step_up
            guardrails_fired.append({
                "rule": "Volatility Dampener",
                "triggered": True,
                "original": round(orig, 2),
                "clipped_to": round(clipped_price, 2),
                "explanation": f"Limited upward adjustment to max {max_price_change_pct:.0f}% per cycle."
            })
        elif clipped_price < max_step_down:
            orig = clipped_price
            clipped_price = max_step_down
            guardrails_fired.append({
                "rule": "Volatility Dampener",
                "triggered": True,
                "original": round(orig, 2),
                "clipped_to": round(clipped_price, 2),
                "explanation": f"Limited downward adjustment to max {max_price_change_pct:.0f}% per cycle."
            })

    # Final safety floor
    clipped_price = max(cost_price, min(mrp, clipped_price))
    guardrail_applied = len(guardrails_fired) > 0

    return clipped_price, guardrail_applied, min_allowed, max_allowed, guardrails_fired

def generate_economic_rationale(
    product_name: str,
    cost_price: float,
    current_price: float,
    mrp: float,
    recommended_price: float,
    competitor_price: Optional[float],
    competitor_name: Optional[str],
    stock_quantity: Optional[int],
    average_daily_sales: Optional[float],
    stock_runway_days: Optional[float],
    margin_current_pct: float,
    margin_recommended_pct: float,
    margin_lift_pct: float,
    competitor_gap_pct: Optional[float],
    confidence_level: str,
    guardrails_fired: List[Dict[str, Any]],
    business_goal: Optional[str] = "balanced"
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Generates rule-based economic rationale without any external paid LLM APIs.
    Strictly reports facts from available user inputs without fabricating missing values.
    """
    insights = []
    drivers = []

    price_diff = recommended_price - current_price
    price_pct = (price_diff / current_price) * 100.0 if current_price > 0 else 0.0

    # 1. Primary Recommendation Statement
    if price_pct > 1.5:
        insights.append(
            f"Recommended price represents a +{price_pct:.1f}% adjustment (₹{current_price:,.2f} → ₹{recommended_price:,.2f}), "
            f"expanding gross margin from {margin_current_pct:.1f}% to {margin_recommended_pct:.1f}%."
        )
        drivers.append({
            "name": "Margin Expansion",
            "impact": "High Positive",
            "direction": "up",
            "detail": f"+{margin_lift_pct:.1f}% gross margin lift"
        })
    elif price_pct < -1.5:
        insights.append(
            f"Recommended price adjusts {price_pct:.1f}% downward (₹{current_price:,.2f} → ₹{recommended_price:,.2f}) "
            f"to stimulate demand velocity and improve market capture."
        )
        drivers.append({
            "name": "Demand Stimulation",
            "impact": "High Volume",
            "direction": "down",
            "detail": f"{abs(price_pct):.1f}% reduction to boost sales velocity"
        })
    else:
        insights.append(
            f"Current selling price of ₹{current_price:,.2f} is balanced against available cost and market parameters."
        )
        drivers.append({
            "name": "Market Equilibrium",
            "impact": "Neutral",
            "direction": "hold",
            "detail": "Price maintained at baseline"
        })

    # 2. Competitor Context (Strictly when provided)
    if competitor_price is not None and competitor_price > 0:
        c_label = competitor_name if competitor_name else "Competitor Market Benchmark"
        if competitor_gap_pct is not None:
            if competitor_gap_pct > 3.0:
                insights.append(
                    f"Current price is {competitor_gap_pct:+.1f}% above {c_label} (₹{competitor_price:,.2f}). "
                    f"Pricing optimization calibrates for competitive price elasticity."
                )
                drivers.append({
                    "name": "Competitor Pressure",
                    "impact": "Moderate",
                    "direction": "down",
                    "detail": f"{competitor_gap_pct:+.1f}% vs {c_label}"
                })
            elif competitor_gap_pct < -3.0:
                insights.append(
                    f"Current price holds a {abs(competitor_gap_pct):.1f}% value advantage under {c_label} (₹{competitor_price:,.2f}). "
                    f"Room identified for margin headroom capture."
                )
                drivers.append({
                    "name": "Value Advantage",
                    "impact": "Opportunity",
                    "direction": "up",
                    "detail": f"{abs(competitor_gap_pct):.1f}% below {c_label}"
                })
            else:
                insights.append(f"Price is aligned within ±3% of {c_label} (₹{competitor_price:,.2f}).")
    else:
        insights.append("Competitor comparison is unavailable because no competitor price was provided.")

    # 3. Inventory Context (Strictly when provided)
    if stock_runway_days is not None:
        if stock_runway_days < 5.0:
            insights.append(
                f"Urgent low inventory runway ({stock_runway_days:.1f} days remaining). "
                f"Scarcity pricing applied to maximize yield and avoid rapid stockout."
            )
            drivers.append({
                "name": "Inventory Scarcity",
                "impact": "High Yield",
                "direction": "up",
                "detail": f"{stock_runway_days:.1f}d stock runway"
            })
        elif stock_runway_days > 45.0:
            insights.append(
                f"High inventory runway ({stock_runway_days:.0f} days remaining). "
                f"Price calibrated to accelerate unit turnover."
            )
            drivers.append({
                "name": "Inventory Clearance",
                "impact": "Velocity Focus",
                "direction": "down",
                "detail": f"{stock_runway_days:.0f}d stock runway"
            })
        else:
            insights.append(f"Inventory runway is healthy at {stock_runway_days:.1f} days.")
    else:
        insights.append("Inventory pressure cannot be evaluated because stock quantity or daily sales was not provided.")

    # 4. Guardrail Adjustments
    for g in guardrails_fired:
        insights.append(f"Guardrail Applied: {g['rule']} — {g['explanation']}")

    # 5. Confidence Statement
    if confidence_level == "high":
        insights.append("Prediction confidence: HIGH — Rich user business parameters provided.")
    elif confidence_level == "medium":
        insights.append("Prediction confidence: MEDIUM — Recommendation generated with selective model baselines.")
    else:
        insights.append("Prediction confidence: LOW — Several optional business inputs missing; model baselines used heavily.")

    return insights, drivers

def generate_profit_topology_simulation(
    cost_price: float,
    current_price: float,
    mrp: float,
    category: str,
    average_daily_sales: Optional[float] = None,
    competitor_price: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Generates 40 discrete points along the Price-Demand-Profit frontier using microeconomic elasticity.
    All outputs are explicitly labeled as model simulations.
    """
    elasticity = CATEGORY_ELASTICITIES.get(category, -1.4)
    base_orders = average_daily_sales if (average_daily_sales is not None and average_daily_sales > 0) else 25.0

    min_p = max(1.0, cost_price * 0.90)
    max_p = max(min_p + 10.0, mrp * 1.05)

    price_steps = np.linspace(min_p, max_p, 40)
    points = []

    for p in price_steps:
        # Microeconomic constant-elasticity demand curve: Q(p) = Q0 * (p / p0)^e
        if current_price > 0:
            price_ratio = p / current_price
            demand = max(0.1, base_orders * (price_ratio ** elasticity))
        else:
            demand = base_orders

        revenue_30d = float(p * demand * 30.0)
        cost_30d = float(cost_price * demand * 30.0)
        profit_30d = float(revenue_30d - cost_30d)
        margin_pct = float(((p - cost_price) / p) * 100.0) if p > 0 else 0.0

        points.append({
            "price": round(float(p), 2),
            "demand_daily": round(float(demand), 1),
            "projected_revenue_30d": round(revenue_30d, 2),
            "projected_profit_30d": round(profit_30d, 2),
            "margin_pct": round(margin_pct, 1),
            "is_below_cost": bool(p < cost_price),
            "is_above_mrp": bool(p > mrp)
        })

    return points

def analyze_product_pricing(
    product_dict: Dict[str, Any],
    user_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main orchestration entry point:
    1. Prepares 57-feature vector with model defaults
    2. Runs LightGBM inference
    3. Runs guardrail validation
    4. Computes deterministic margin, gap, runway, and projections
    5. Classifies confidence and resolves provenance
    6. Constructs data-driven profit topology simulation
    7. Generates transparent rule-based rationale
    """
    cost_price = float(product_dict["cost_price"])
    current_price = float(product_dict["current_price"])
    mrp = float(product_dict["mrp"])
    category = product_dict.get("category") or "Electronics"
    city = product_dict.get("location") or product_dict.get("city") or "Ahmedabad"

    competitor_price = product_dict.get("competitor_price")
    if competitor_price is None:
        competitor_price = product_dict.get("competitor_avg_price")
    if competitor_price is not None:
        competitor_price = float(competitor_price)

    stock_quantity = product_dict.get("stock_quantity")
    if stock_quantity is None:
        stock_quantity = product_dict.get("stock_level")
    if stock_quantity is not None:
        stock_quantity = int(stock_quantity)

    average_daily_sales = product_dict.get("average_daily_sales")
    if average_daily_sales is None:
        average_daily_sales = product_dict.get("orders")
    if average_daily_sales is not None:
        average_daily_sales = float(average_daily_sales)

    # 1. Build ML payload
    ml_payload = {
        "cost_price": cost_price,
        "current_price": current_price,
        "mrp": mrp,
        "category": category,
        "city": city,
        "competitor_avg_price": competitor_price if competitor_price is not None else current_price,
        "stock_level": stock_quantity if stock_quantity is not None else 100,
        "orders": int(average_daily_sales) if average_daily_sales is not None else 45,
        "days_until_next_festival": product_dict.get("days_until_next_festival") if product_dict.get("days_until_next_festival") is not None else 30,
        "weather_type": product_dict.get("weather_type") or "Clear",
        "competitor_stock_status": product_dict.get("competitor_stock_status") or "In_Stock"
    }

    bundle = get_model_bundle()
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    X = prepare_feature_vector(ml_payload, bundle)
    raw_prediction = float(model.predict(X)[0])

    # 2. Guardrails
    recommended_price, guardrail_applied, min_allowed, max_allowed, guardrails_fired = run_guardrail_checks(
        raw_price=raw_prediction,
        cost_price=cost_price,
        current_price=current_price,
        mrp=mrp,
        competitor_price=competitor_price,
        settings=user_settings
    )

    # 3. Deterministic Metrics
    price_change = recommended_price - current_price
    price_change_pct = (price_change / current_price) * 100.0 if current_price > 0 else 0.0

    margin_current_pct = ((current_price - cost_price) / current_price) * 100.0 if current_price > 0 else 0.0
    margin_recommended_pct = ((recommended_price - cost_price) / recommended_price) * 100.0 if recommended_price > 0 else 0.0
    margin_lift_pct = margin_recommended_pct - margin_current_pct

    competitor_gap_pct = None
    if competitor_price is not None and competitor_price > 0:
        competitor_gap_pct = ((current_price - competitor_price) / competitor_price) * 100.0

    stock_runway_days = None
    if stock_quantity is not None and average_daily_sales is not None and average_daily_sales > 0:
        stock_runway_days = float(stock_quantity) / float(average_daily_sales)

    # 30-day Projections
    elasticity = CATEGORY_ELASTICITIES.get(category, -1.4)
    expected_demand = None
    expected_revenue_30d = None
    expected_profit_30d = None

    if average_daily_sales is not None and average_daily_sales > 0 and current_price > 0:
        price_ratio = recommended_price / current_price
        demand_factor = max(0.1, price_ratio ** elasticity)
        expected_demand = float(average_daily_sales * demand_factor)
        expected_revenue_30d = float(recommended_price * expected_demand * 30.0)
        expected_profit_30d = float((recommended_price - cost_price) * expected_demand * 30.0)

    # 4. Confidence & Provenance
    confidence_level, confidence_details = classify_prediction_confidence(product_dict)
    feature_provenance = resolve_feature_provenance(product_dict)

    # 5. Recommendation Action Label
    if price_change_pct > 1.5:
        recommendation = "Increase Price"
    elif price_change_pct < -1.5:
        recommendation = "Decrease Price"
    else:
        recommendation = "Hold Price"

    # 6. Rationale
    insights, economic_drivers = generate_economic_rationale(
        product_name=product_dict.get("product_name", "Target SKU"),
        cost_price=cost_price,
        current_price=current_price,
        mrp=mrp,
        recommended_price=recommended_price,
        competitor_price=competitor_price,
        competitor_name=product_dict.get("competitor_name"),
        stock_quantity=stock_quantity,
        average_daily_sales=average_daily_sales,
        stock_runway_days=stock_runway_days,
        margin_current_pct=margin_current_pct,
        margin_recommended_pct=margin_recommended_pct,
        margin_lift_pct=margin_lift_pct,
        competitor_gap_pct=competitor_gap_pct,
        confidence_level=confidence_level,
        guardrails_fired=guardrails_fired,
        business_goal=product_dict.get("business_goal", "balanced")
    )

    # 7. Profit Topology Simulation
    topology_curve = generate_profit_topology_simulation(
        cost_price=cost_price,
        current_price=current_price,
        mrp=mrp,
        category=category,
        average_daily_sales=average_daily_sales,
        competitor_price=competitor_price
    )

    return {
        "recommended_price": round(recommended_price, 2),
        "price_change": round(price_change, 2),
        "price_change_pct": round(price_change_pct, 2),
        "recommendation": recommendation,
        "margin_current_pct": round(margin_current_pct, 2),
        "margin_recommended_pct": round(margin_recommended_pct, 2),
        "margin_lift_pct": round(margin_lift_pct, 2),
        "competitor_gap_pct": round(competitor_gap_pct, 2) if competitor_gap_pct is not None else None,
        "stock_runway_days": round(stock_runway_days, 1) if stock_runway_days is not None else None,
        "expected_demand": round(expected_demand, 2) if expected_demand is not None else None,
        "expected_revenue_30d": round(expected_revenue_30d, 2) if expected_revenue_30d is not None else None,
        "expected_profit_30d": round(expected_profit_30d, 2) if expected_profit_30d is not None else None,
        "confidence_level": confidence_level,
        "confidence_details": confidence_details,
        "guardrail_applied": guardrail_applied,
        "guardrail_details": guardrails_fired,
        "min_allowed_price": round(min_allowed, 2),
        "max_allowed_price": round(max_allowed, 2),
        "insights": insights,
        "economic_drivers": economic_drivers,
        "feature_provenance": feature_provenance,
        "topology_curve": topology_curve
    }
