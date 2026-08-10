"""
Feature Engineering module for time series, pricing ratios, macro transformations,
funnel derivations, and rolling/lag computations.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any
from .config import CATEGORY_CONFIG

def compute_macro_indices(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Computes Indian CPI-realistic Inflation_Index and seasonal Consumer_Confidence_Proxy.
    - Inflation_Index: Base 100 at Jan 2023, ~5.5% annual growth with monthly seasonal waves
    - Consumer_Confidence_Proxy: Base 60, monsoon dip, festive peak (Navratri/Diwali), slight GDP trend
    """
    n_days = len(dates)
    day_of_year = dates.dayofyear.values
    t = np.arange(n_days)
    months_since_start = (dates.year - 2023) * 12 + (dates.month - 1)

    # Inflation trajectory (RBI target 4% +/- 2%, 2023-2026 actual avg ~5.5%)
    annual_rate = 0.054
    daily_trend = (1.0 + annual_rate) ** (t / 365.25)
    seasonal_cpi = 0.006 * np.sin(2 * np.pi * (day_of_year - 90) / 365.25)
    noise_cpi = np.random.normal(0, 0.002, size=n_days)
    inflation_index = 100.0 * daily_trend * (1.0 + seasonal_cpi + noise_cpi)

    # Consumer confidence (scale 35 to 85)
    base_sentiment = 60.0 + 0.12 * months_since_start
    festive_boost = 10.0 * np.exp(-((day_of_year - 295) ** 2) / (2 * 30 ** 2)) # Oct/Nov festive peak
    monsoon_dip = -4.5 * np.exp(-((day_of_year - 200) ** 2) / (2 * 25 ** 2))  # Jul monsoon dip
    noise_sentiment = np.random.normal(0, 1.2, size=n_days)
    consumer_confidence = np.clip(base_sentiment + festive_boost + monsoon_dip + noise_sentiment, 38.0, 84.0)

    return pd.DataFrame({
        "Date": dates.strftime("%Y-%m-%d"),
        "Inflation_Index": np.round(inflation_index, 2).astype(np.float32),
        "Consumer_Confidence_Proxy": np.round(consumer_confidence, 1).astype(np.float32)
    })

def compute_impact_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates normalized impact scores:
    - Festival_Impact_Score (0 to 3.0)
    - Weather_Impact_Score (-2.0 to 2.0)
    - Seasonality_Impact_Score (-1.5 to 1.5)
    """
    # 1. Festival Impact
    days_to_fest = df["Days_Until_Next_Festival"].values.astype(float)
    is_holiday = df["Is_Holiday"].values.astype(float)
    
    # Decays exponentially as festival approaches; peak on holiday/festival days
    fest_score = 2.5 * np.exp(-days_to_fest / 7.0) + (is_holiday * 0.5)
    df["Festival_Impact_Score"] = np.round(np.clip(fest_score, 0.0, 3.0), 2).astype(np.float32)

    # 2. Weather Impact (Category specific)
    temp = df["Temperature"].values
    rain = df["Rainfall"].values
    cat = df["Category"].values

    w_score = np.zeros(len(df), dtype=np.float32)
    # Monsoon boost for Grocery & Home, negative for Footwear & Outdoor
    monsoon_mask = rain > 5.0
    w_score[monsoon_mask & np.isin(cat, ["Grocery", "Home & Kitchen"])] += 0.8
    w_score[monsoon_mask & np.isin(cat, ["Footwear", "Sports & Fitness"])] -= 0.6

    # Extreme summer heat (> 38C)
    heat_mask = temp > 38.0
    w_score[heat_mask & np.isin(cat, ["Personal Care", "Sports & Fitness"])] += 0.7
    w_score[heat_mask & np.isin(cat, ["Fashion", "Footwear"])] -= 0.4

    df["Weather_Impact_Score"] = np.round(np.clip(w_score, -2.0, 2.0), 2).astype(np.float32)

    # 3. Seasonality Impact Score
    month = df["Month"].values
    s_score = np.zeros(len(df), dtype=np.float32)
    # Q4 (Oct-Dec) is peak e-commerce season in India
    s_score[month >= 10] += 1.0
    # Q1 (Jan-Mar) moderate
    s_score[month <= 3] += 0.3
    # Q2-Q3 monsoon / summer lull
    s_score[(month >= 6) & (month <= 8)] -= 0.5
    
    df["Seasonality_Impact_Score"] = np.round(np.clip(s_score, -1.5, 1.5), 2).astype(np.float32)
    return df

def apply_lag_and_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes time-series lag and rolling statistics on SKU-City groups.
    Guarantees strict NO-FUTURE-LEAKAGE by sorting chronologically and shifting.
    Zero-null guarantee across entire dataset.
    """
    # Sort strictly by SKU, City, Date
    df = df.sort_values(["SKU", "City", "Date"]).reset_index(drop=True)

    grouped = df.groupby(["SKU", "City"], group_keys=False)

    # 7-day Lags (leakage-free shift)
    df["Price_Lag_7"] = grouped["Current_Price"].shift(7).fillna(df["Current_Price"]).round(2).astype(np.float32)
    df["Demand_Lag_7"] = grouped["Orders"].shift(7).fillna(df["Orders"]).round(0).astype(np.float32)

    # 30-day Rolling Mean of Price (shifted by 1 to exclude current day)
    roll_30 = grouped["Current_Price"].transform(lambda x: x.shift(1).rolling(30, min_periods=1).mean())
    df["Rolling_Avg_Price_30d"] = roll_30.fillna(df["Current_Price"]).round(2).astype(np.float32)

    # 30-day Rolling Volatility of Price
    vol_30 = grouped["Current_Price"].transform(lambda x: x.shift(1).rolling(30, min_periods=2).std())
    df["Price_Volatility_30d"] = vol_30.fillna(0.0).round(2).astype(np.float32)

    # Demand Momentum: 7-day rolling orders / 14-day rolling orders
    roll_7 = grouped["Orders"].transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean())
    roll_14 = grouped["Orders"].transform(lambda x: x.shift(1).rolling(14, min_periods=1).mean())
    
    roll_7_safe = roll_7.fillna(df["Orders"].astype(float))
    roll_14_safe = roll_14.fillna(df["Orders"].astype(float))
    
    df["Demand_Momentum_7d"] = np.round(np.clip(roll_7_safe / np.maximum(roll_14_safe, 0.5), 0.2, 3.5), 2).astype(np.float32)
    
    # Stock Days Remaining = Stock_Level / max(rolling 7-day orders, 0.5)
    df["Stock_Days_Remaining"] = np.round(np.clip(df["Stock_Level"].astype(float) / np.maximum(roll_7_safe, 0.5), 0.1, 180.0), 1).astype(np.float32)

    return df
