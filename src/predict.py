"""
Prediction Pipeline for Real-Time Dynamic Price Optimization Engine.
Loads the trained model bundle, validates incoming requests, prepares features,
executes inference, applies strict business guardrails, and returns actionable recommendations.
"""
import os
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "price_optimizer.pkl"

# Global cached model bundle
_MODEL_BUNDLE: Optional[Dict[str, Any]] = None

def get_model_bundle() -> Dict[str, Any]:
    """
    Loads and caches the model bundle in memory for low-latency inference.
    """
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Please train the model first.")
        with open(MODEL_PATH, "rb") as f:
            _MODEL_BUNDLE = pickle.load(f)
    return _MODEL_BUNDLE

def validate_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates that all essential retail pricing fields are provided with sensible values.
    """
    required_fields = ["cost_price", "current_price", "mrp", "competitor_avg_price"]
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Missing required pricing field: '{field}'")
        if float(data[field]) <= 0:
            raise ValueError(f"Pricing field '{field}' must be strictly positive.")

    cost_price = float(data["cost_price"])
    current_price = float(data["current_price"])
    mrp = float(data["mrp"])

    if cost_price > mrp:
        raise ValueError(f"Cost price (INR {cost_price:.2f}) cannot exceed MRP (INR {mrp:.2f}).")

    return data

def prepare_feature_vector(data: Dict[str, Any], bundle: Dict[str, Any]) -> np.ndarray:
    """
    Transforms raw input dictionary into the canonical 57-feature vector expected by the model.
    """
    feature_cols: List[str] = bundle["feature_columns"]
    cat_map = bundle["category_mapping"]
    city_map = bundle["city_mapping"]
    weather_map = bundle["weather_mapping"]
    comp_stock_map = bundle["competitor_stock_mapping"]

    # Core pricing numbers
    cost_price = float(data.get("cost_price", 500.0))
    current_price = float(data.get("current_price", 800.0))
    mrp = float(data.get("mrp", 1000.0))
    marketplace_fee_pct = float(data.get("marketplace_fee_pct", 12.0))
    competitor_avg_price = float(data.get("competitor_avg_price", current_price))
    competitor_min_price = float(data.get("competitor_min_price", competitor_avg_price * 0.94))
    competitor_discount_pct = float(data.get("competitor_discount_pct", 15.0))

    # Derived Pricing Ratios
    discount_pct = max(0.0, min(75.0, (mrp - current_price) / mrp * 100.0))
    margin_pct = (current_price - cost_price) / current_price * 100.0
    price_gap_pct = (current_price - competitor_avg_price) / max(competitor_avg_price, 1.0) * 100.0
    price_to_comp_ratio = current_price / max(competitor_avg_price, 1.0)

    # Market Rank (1 to 5)
    if price_gap_pct < -8.0:
        market_rank = 1
    elif price_gap_pct < -2.0:
        market_rank = 2
    elif price_gap_pct < 3.0:
        market_rank = 3
    elif price_gap_pct < 8.0:
        market_rank = 4
    else:
        market_rank = 5

    # Inventory Features
    stock_level = int(data.get("stock_level", 150))
    reorder_point = int(data.get("reorder_point", 50))
    lead_time_days = int(data.get("lead_time_days", 5))
    stock_out_risk = float(np.clip((reorder_point - stock_level) / max(reorder_point, 1), 0.0, 1.0))
    
    daily_orders = float(data.get("orders", 45.0))
    stock_days_remaining = float(np.clip(stock_level / max(daily_orders, 0.5), 0.1, 180.0))

    # Categoricals
    category = str(data.get("category", "Electronics"))
    category_code = cat_map.get(category, 0)

    city = str(data.get("city", "Ahmedabad"))
    city_code = city_map.get(city, 0)

    weather_type = str(data.get("weather_type", "Clear"))
    weather_code = weather_map.get(weather_type, 0)

    comp_stock = str(data.get("competitor_stock_status", "In_Stock"))
    comp_stock_code = comp_stock_map.get(comp_stock, 0)

    # Temporal & Festival
    day_of_week = int(data.get("day_of_week", 2))
    month = int(data.get("month", 8))
    quarter = int(data.get("quarter", 3))
    is_weekend = int(data.get("is_weekend", day_of_week in [5, 6]))
    is_holiday = int(data.get("is_holiday", 0))
    is_month_end = int(data.get("is_month_end", 0))
    days_until_festival = int(data.get("days_until_next_festival", 45))
    days_since_launch = int(data.get("days_since_launch", 300))
    days_since_price_change = int(data.get("days_since_last_price_change", 5))

    # Weather
    temperature = float(data.get("temperature", 32.5))
    humidity = float(data.get("humidity", 65.0))
    rainfall = float(data.get("rainfall", 0.0))
    is_extreme_weather = int(temperature >= 44.0 or rainfall >= 50.0)

    # Macroeconomics (defaults reflecting Gujarat benchmarks)
    usd_inr = float(data.get("usd_inr", 89.20))
    crude_oil = float(data.get("crude_oil_price_usd", 78.50))
    gold_price = float(data.get("gold_price", 2400.0))
    inflation_index = float(data.get("inflation_index", 118.5))
    consumer_confidence = float(data.get("consumer_confidence_proxy", 65.0))
    fuel_price_proxy = float(data.get("fuel_price_inr_proxy", crude_oil * usd_inr * 0.017))

    # Demand Signals
    orders = int(daily_orders)
    views = int(data.get("views", max(500, orders * 150)))
    clicks = int(data.get("clicks", max(orders * 15, int(views * 0.12))))
    cart_adds = int(data.get("cart_adds", max(orders * 3, int(clicks * 0.22))))
    conversion_rate = float(round((orders / max(clicks, 1)) * 100.0, 2))
    search_trend_index = float(data.get("search_trend_index", 50.0))
    demand_index = float(round((orders * 0.50 + cart_adds * 0.25 + clicks * 0.15 + (views / 10.0) * 0.10) / 10.0, 2))
    return_rate = float(data.get("return_rate", 5.0))

    # Historical Lags & Volatility
    price_lag_7 = float(data.get("price_lag_7", current_price))
    demand_lag_7 = float(data.get("demand_lag_7", orders))
    rolling_avg_price_30d = float(data.get("rolling_avg_price_30d", current_price))
    price_volatility_30d = float(data.get("price_volatility_30d", 12.5))
    demand_momentum_7d = float(data.get("demand_momentum_7d", 1.05))

    # Economic & Impact Scores
    # Default category elasticity seeds
    elasticity_defaults = {
        "Grocery": -1.0, "Personal Care": -1.2, "Home & Kitchen": -1.4,
        "Footwear": -1.6, "Sports & Fitness": -1.7, "Fashion": -1.9,
        "Mobile Accessories": -2.0, "Electronics": -2.2
    }
    price_elasticity_score = float(data.get("price_elasticity_score", elasticity_defaults.get(category, -1.8)))

    # Festival impact calculation
    fest_score = 2.5 * np.exp(-days_until_festival / 7.0) + (is_holiday * 0.5)
    festival_impact_score = float(round(np.clip(fest_score, 0.0, 3.0), 2))

    # Weather impact
    w_score = 0.0
    if rainfall > 5.0 and category in ["Grocery", "Home & Kitchen"]:
        w_score += 0.8
    elif rainfall > 5.0 and category in ["Footwear", "Sports & Fitness"]:
        w_score -= 0.6
    if temperature > 38.0 and category in ["Personal Care", "Sports & Fitness"]:
        w_score += 0.7
    weather_impact_score = float(round(np.clip(w_score, -2.0, 2.0), 2))

    # Seasonality impact
    s_score = 0.0
    if month >= 10:
        s_score += 1.0
    elif month <= 3:
        s_score += 0.3
    elif 6 <= month <= 8:
        s_score -= 0.5
    seasonality_impact_score = float(round(np.clip(s_score, -1.5, 1.5), 2))

    # Construct feature dictionary mapping exactly to 57 features
    feature_dict = {
        "Cost_Price": cost_price,
        "Current_Price": current_price,
        "MRP": mrp,
        "Marketplace_Fee_Pct": marketplace_fee_pct,
        "Competitor_Avg_Price": competitor_avg_price,
        "Competitor_Min_Price": competitor_min_price,
        "Price_Gap_Pct": price_gap_pct,
        "Price_to_Competitor_Ratio": price_to_comp_ratio,
        "Competitor_Discount_Pct": competitor_discount_pct,
        "Market_Rank": market_rank,
        "Discount_Pct": discount_pct,
        "Margin_Pct": margin_pct,
        "Stock_Level": stock_level,
        "Reorder_Point": reorder_point,
        "Lead_Time_Days": lead_time_days,
        "Stock_Out_Risk": stock_out_risk,
        "Stock_Days_Remaining": stock_days_remaining,
        "Category_Code": category_code,
        "City_Code": city_code,
        "Weather_Code": weather_code,
        "Competitor_Stock_Code": comp_stock_code,
        "Day_of_Week": day_of_week,
        "Month": month,
        "Quarter": quarter,
        "Is_Weekend": is_weekend,
        "Is_Holiday": is_holiday,
        "Is_Month_End": is_month_end,
        "Days_Until_Next_Festival": days_until_festival,
        "Days_Since_Launch": days_since_launch,
        "Days_Since_Last_Price_Change": days_since_price_change,
        "Temperature": temperature,
        "Humidity": humidity,
        "Rainfall": rainfall,
        "Is_Extreme_Weather": is_extreme_weather,
        "USD_INR": usd_inr,
        "Crude_Oil_Price_USD": crude_oil,
        "Gold_Price": gold_price,
        "Inflation_Index": inflation_index,
        "Consumer_Confidence_Proxy": consumer_confidence,
        "Fuel_Price_INR_Proxy": fuel_price_proxy,
        "Views": views,
        "Clicks": clicks,
        "Cart_Adds": cart_adds,
        "Orders": orders,
        "Conversion_Rate": conversion_rate,
        "Search_Trend_Index": search_trend_index,
        "Demand_Index": demand_index,
        "Return_Rate": return_rate,
        "Price_Lag_7": price_lag_7,
        "Demand_Lag_7": demand_lag_7,
        "Rolling_Avg_Price_30d": rolling_avg_price_30d,
        "Price_Volatility_30d": price_volatility_30d,
        "Demand_Momentum_7d": demand_momentum_7d,
        "Price_Elasticity_Score": price_elasticity_score,
        "Festival_Impact_Score": festival_impact_score,
        "Weather_Impact_Score": weather_impact_score,
        "Seasonality_Impact_Score": seasonality_impact_score
    }

    # Verify all 57 columns are present in canonical order
    vec = np.array([[feature_dict[col] for col in feature_cols]], dtype=np.float32)
    return vec

def apply_business_guardrails(raw_price: float, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforces operational retail guardrails:
    1. Margin floor: Price >= Cost Price * 1.05
    2. Catalog boundaries: [Min_Allowed_Price, Max_Allowed_Price]
    3. Competitor corridor: [0.75 * Comp_Avg, 1.25 * Comp_Avg]
    """
    cost_price = float(data.get("cost_price", 500.0))
    mrp = float(data.get("mrp", 1000.0))
    comp_avg = float(data.get("competitor_avg_price", cost_price * 1.5))
    
    min_allowed = float(data.get("min_allowed_price", cost_price * 1.05))
    max_allowed = float(data.get("max_allowed_price", mrp * 1.05))

    # Guardrail calculations
    lower_bound = max(min_allowed, cost_price * 1.05, comp_avg * 0.75)
    upper_bound = min(max_allowed, comp_avg * 1.25)
    upper_bound = max(upper_bound, lower_bound)

    clipped_price = float(np.clip(raw_price, lower_bound, upper_bound))
    clipped_price = round(clipped_price, 2)

    return {
        "final_price": clipped_price,
        "lower_bound": round(lower_bound, 2),
        "upper_bound": round(upper_bound, 2),
        "clipped": clipped_price != round(raw_price, 2)
    }

def generate_business_insights(data: Dict[str, Any], rec_price: float, curr_price: float, guardrail_info: Dict[str, Any]) -> List[str]:
    """
    Generates human-readable, commercial merchandising insights for retail decision makers.
    """
    insights = []
    diff_pct = (rec_price - curr_price) / curr_price * 100.0
    stock_level = int(data.get("stock_level", 100))
    daily_orders = max(float(data.get("orders", 30.0)), 1.0)
    stock_days = stock_level / daily_orders
    days_to_fest = int(data.get("days_until_next_festival", 45))
    comp_avg = float(data.get("competitor_avg_price", curr_price))

    if diff_pct > 2.0:
        insights.append(f"Recommended price represents a {diff_pct:+.1f}% margin expansion opportunity.")
    elif diff_pct < -2.0:
        insights.append(f"Recommended price adjusts {diff_pct:.1f}% to stimulate sales velocity and protect market share.")
    else:
        insights.append("Current pricing is well-optimized for prevailing market conditions.")

    if stock_days < 4.0:
        insights.append(f"Inventory runway is low ({stock_days:.1f} days remaining); pricing includes a scarcity premium.")
    elif stock_days > 60.0:
        insights.append(f"High warehouse inventory ({stock_days:.0f} days remaining); competitive pricing recommended to accelerate stock turnover.")

    if days_to_fest <= 7:
        insights.append("Regional festive demand surge detected in Gujarat; capturing higher margin realization.")

    if curr_price > comp_avg * 1.05:
        insights.append("Product is currently priced above market consensus; optimizer calibrated competitive elasticity.")
    elif curr_price < comp_avg * 0.95:
        insights.append("Product holds a value-pricing advantage relative to competitors.")

    insights.append(f"Pricing strictly adheres to guaranteed profit floor (>= INR {guardrail_info['lower_bound']:.2f}).")
    return insights

def predict_optimal_price(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    End-to-End Prediction Function:
    Input -> Validate -> Feature Extraction -> LightGBM Inference -> Guardrails -> Recommendation
    """
    # 1. Validation
    validated = validate_input_data(input_data)
    curr_price = float(validated["current_price"])

    # 2. Model & Features
    bundle = get_model_bundle()
    model = bundle["model"]
    feature_vec = prepare_feature_vector(validated, bundle)

    # 3. Model Inference
    raw_prediction = float(model.predict(feature_vec)[0])

    # 4. Business Guardrails
    guardrails = apply_business_guardrails(raw_prediction, validated)
    recommended_price = guardrails["final_price"]

    # 5. Recommendation Action
    price_change = round(recommended_price - curr_price, 2)
    price_change_pct = round((price_change / curr_price) * 100.0, 2)

    if price_change_pct > 2.0:
        recommendation = "Increase Price"
    elif price_change_pct < -2.0:
        recommendation = "Decrease Price"
    else:
        recommendation = "Hold Price"

    # 6. Insights
    insights = generate_business_insights(validated, recommended_price, curr_price, guardrails)

    return {
        "current_price": curr_price,
        "recommended_price": recommended_price,
        "price_change": price_change,
        "price_change_percentage": price_change_pct,
        "recommendation": recommendation,
        "guardrail_applied": guardrails["clipped"],
        "min_allowed_price": guardrails["lower_bound"],
        "max_allowed_price": guardrails["upper_bound"],
        "insights": insights
    }
