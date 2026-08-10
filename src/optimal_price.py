"""
Vectorized Optimal_Price computation using closed-form microeconomic profit maximization
p* = c / (1 + 1/epsilon) augmented with contextual multipliers and competitive/margin bounds.
"""
import numpy as np
import pandas as pd

def compute_optimal_price(df: pd.DataFrame) -> np.ndarray:
    """
    Computes Optimal_Price across the entire DataFrame in a fully vectorized manner.
    
    Formula Steps:
    1. Effective variable unit cost c = Cost_Price * (1 + Marketplace_Fee_Pct / 100)
    2. Base Optimal p* = c / (1 + 1 / Price_Elasticity_Score)
    3. Context Adjustments (Festivals, Weather, Seasonality, Competitor price anchor)
    4. Inventory Scarcity / Overstock adjustments based on Stock_Days_Remaining
    5. Safeguard clipping to [Min_Allowed_Price, Max_Allowed_Price] with competitor corridor
    """
    cost_price = df["Cost_Price"].values.astype(np.float64)
    fee_pct = df["Marketplace_Fee_Pct"].values.astype(np.float64)
    elasticity = df["Price_Elasticity_Score"].values.astype(np.float64)
    
    competitor_avg = df["Competitor_Avg_Price"].values.astype(np.float64)
    min_allowed = df["Min_Allowed_Price"].values.astype(np.float64)
    max_allowed = df["Max_Allowed_Price"].values.astype(np.float64)
    
    festival_impact = df["Festival_Impact_Score"].values.astype(np.float64)
    weather_impact = df["Weather_Impact_Score"].values.astype(np.float64)
    seasonality_impact = df["Seasonality_Impact_Score"].values.astype(np.float64)
    stock_days_remaining = df["Stock_Days_Remaining"].values.astype(np.float64)

    # Step 1: Total variable unit cost including platform take-rate
    c = cost_price * (1.0 + fee_pct / 100.0)

    # Step 2: Unconstrained monopoly base price from constant elasticity demand
    # Elasticity epsilon < -1.0, so 1 + 1/epsilon is positive and < 1.0
    # Guard against epsilon >= -1.0 or division anomalies
    safe_elasticity = np.clip(elasticity, -10.0, -1.01)
    markup_factor = 1.0 / (1.0 + (1.0 / safe_elasticity))
    base_optimal = c * markup_factor

    # Step 3: Context Multipliers
    festival_mult = 1.0 + (festival_impact * 0.05)
    weather_mult = 1.0 + (weather_impact * 0.02)
    seasonality_mult = 1.0 + (seasonality_impact * 0.03)

    # Competitor anchor: prevents model from straying unrealistically far from market consensus
    comp_ratio = competitor_avg / np.maximum(base_optimal, 1.0)
    competitor_anchor = np.clip(comp_ratio, 0.85, 1.15)

    adjusted_price = base_optimal * festival_mult * weather_mult * seasonality_mult * competitor_anchor

    # Step 4: Inventory Urgency Multiplier
    # Scarcity premium if stock is running out (< 3 days), markdown discount if overstocked (> 90 days)
    inventory_mult = np.ones_like(adjusted_price)
    inventory_mult = np.where(stock_days_remaining < 3.0, inventory_mult * 1.10, inventory_mult)
    inventory_mult = np.where(stock_days_remaining > 90.0, inventory_mult * 0.95, inventory_mult)

    final_candidate = adjusted_price * inventory_mult

    # Step 5: Safeguard Bounds & Margin Floor Protection
    # Competitor corridor: [0.75 * Comp_Avg, 1.25 * Comp_Avg]
    # Margin floor: Must be at least 5% above raw Cost_Price
    margin_floor = cost_price * 1.05
    lower_bound = np.maximum(min_allowed, competitor_avg * 0.75)
    lower_bound = np.maximum(lower_bound, margin_floor)

    upper_bound = np.minimum(max_allowed, competitor_avg * 1.25)
    upper_bound = np.maximum(upper_bound, lower_bound)  # Ensure upper >= lower

    optimal_price = np.clip(final_candidate, lower_bound, upper_bound)
    return np.round(optimal_price, 2).astype(np.float32)
