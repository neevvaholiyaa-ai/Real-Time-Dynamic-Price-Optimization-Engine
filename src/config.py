"""
Configuration and constants for the Real-Time Dynamic Price Optimization Engine dataset pipeline.
"""
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Output Deliverables
CSV_OUTPUT_PATH = DATA_DIR / "dataset.csv"
PARQUET_OUTPUT_PATH = DATA_DIR / "dataset.parquet"
METADATA_PATH = DATA_DIR / "metadata.json"
DATA_DICTIONARY_PATH = PROJECT_ROOT / "data_dictionary.md"
VALIDATION_REPORT_PATH = DATA_DIR / "validation_report.json"
REJECTED_ROWS_PATH = DATA_DIR / "rejected_rows.csv"
DATA_QUALITY_REPORT_PATH = DATA_DIR / "data_quality_report.md"
README_PATH = PROJECT_ROOT / "README.md"

# Intermediate files (will be auto-cleaned after pipeline finishes successfully)
SQLITE_CACHE_PATH = DATA_DIR / "api_cache.db"
CHECKPOINT_PATH = DATA_DIR / "checkpoint.json"

# Date Bounds
START_DATE = "2023-01-01"
END_DATE = "2026-08-02"  # Capped 7 days before today to prevent Open-Meteo archive lag

# Target Row Range
MIN_TARGET_ROWS = 80_000
MAX_TARGET_ROWS = 150_000
BATCH_SIZE = 10_000

# Geographic Configuration
CITIES = {
    "Ahmedabad": {
        "latitude": 23.0300,
        "longitude": 72.5800,
        "state": "Gujarat",
        "warehouses": ["WH-AMD-01", "WH-AMD-02"],
        "base_traffic_multiplier": 1.15,
        "tier": "Tier-1 Metro"
    },
    "Surat": {
        "latitude": 21.1700,
        "longitude": 72.8300,
        "state": "Gujarat",
        "warehouses": ["WH-SUR-01"],
        "base_traffic_multiplier": 0.95,
        "tier": "Tier-2 Commercial Hub"
    }
}

# Category Settings & Single Source of Truth Elasticity Seeds
CATEGORY_CONFIG = {
    "Grocery": {
        "seeded_elasticity": -1.0,
        "marketplace_fee_pct": 8.0,
        "avg_margin_pct": 18.0,
        "reorder_lead_time_days": (2, 5),
        "competitor_price_sigma": 0.03,
        "search_trend_keyword": "grocery delivery online India"
    },
    "Personal Care": {
        "seeded_elasticity": -1.2,
        "marketplace_fee_pct": 10.0,
        "avg_margin_pct": 28.0,
        "reorder_lead_time_days": (3, 7),
        "competitor_price_sigma": 0.04,
        "search_trend_keyword": "skin care products online India"
    },
    "Home & Kitchen": {
        "seeded_elasticity": -1.4,
        "marketplace_fee_pct": 14.0,
        "avg_margin_pct": 32.0,
        "reorder_lead_time_days": (5, 10),
        "competitor_price_sigma": 0.05,
        "search_trend_keyword": "kitchen appliances online India"
    },
    "Footwear": {
        "seeded_elasticity": -1.6,
        "marketplace_fee_pct": 13.0,
        "avg_margin_pct": 35.0,
        "reorder_lead_time_days": (4, 9),
        "competitor_price_sigma": 0.06,
        "search_trend_keyword": "shoes online shopping India"
    },
    "Sports & Fitness": {
        "seeded_elasticity": -1.7,
        "marketplace_fee_pct": 12.0,
        "avg_margin_pct": 30.0,
        "reorder_lead_time_days": (4, 8),
        "competitor_price_sigma": 0.05,
        "search_trend_keyword": "gym fitness equipment India"
    },
    "Fashion": {
        "seeded_elasticity": -1.9,
        "marketplace_fee_pct": 15.0,
        "avg_margin_pct": 42.0,
        "reorder_lead_time_days": (4, 10),
        "competitor_price_sigma": 0.07,
        "search_trend_keyword": "fashion clothing online India"
    },
    "Mobile Accessories": {
        "seeded_elasticity": -2.0,
        "marketplace_fee_pct": 16.0,
        "avg_margin_pct": 45.0,
        "reorder_lead_time_days": (3, 7),
        "competitor_price_sigma": 0.08,
        "search_trend_keyword": "mobile phone accessories online India"
    },
    "Electronics": {
        "seeded_elasticity": -2.2,
        "marketplace_fee_pct": 12.0,
        "avg_margin_pct": 22.0,
        "reorder_lead_time_days": (5, 12),
        "competitor_price_sigma": 0.06,
        "search_trend_keyword": "electronics gadget sale India"
    }
}

# Launch Cohorts Specification (9 cohorts, 130 SKUs total)
COHORT_SCHEDULE = [
    {"cohort_id": "C1", "launch_date": "2023-01-15", "sku_count": 4},
    {"cohort_id": "C2", "launch_date": "2023-08-01", "sku_count": 4},
    {"cohort_id": "C3", "launch_date": "2024-02-01", "sku_count": 8},
    {"cohort_id": "C4", "launch_date": "2024-06-01", "sku_count": 10},
    {"cohort_id": "C5", "launch_date": "2024-10-01", "sku_count": 14},
    {"cohort_id": "C6", "launch_date": "2025-02-01", "sku_count": 18},
    {"cohort_id": "C7", "launch_date": "2025-05-01", "sku_count": 22},
    {"cohort_id": "C8", "launch_date": "2025-07-01", "sku_count": 25},
    {"cohort_id": "C9", "launch_date": "2025-08-15", "sku_count": 25},
]

# Total Columns Definition: 71 Columns
COLUMN_SCHEMA = {
    # Group 1 — Identifiers (8 columns)
    "Product_ID": {"dtype": "string", "source_tag": "simulated_documented", "group": "Identifiers"},
    "Product_Name": {"dtype": "string", "source_tag": "simulated_documented", "group": "Identifiers"},
    "Brand": {"dtype": "string", "source_tag": "simulated_documented", "group": "Identifiers"},
    "Category": {"dtype": "string", "source_tag": "simulated_documented", "group": "Identifiers"},
    "Subcategory": {"dtype": "string", "source_tag": "simulated_documented", "group": "Identifiers"},
    "SKU": {"dtype": "string", "source_tag": "simulated_documented", "group": "Identifiers"},
    "City": {"dtype": "string", "source_tag": "simulated_documented", "group": "Identifiers"},
    "Date": {"dtype": "date", "source_tag": "simulated_documented", "group": "Identifiers"},

    # Group 2 — Temporal (10 columns)
    "Day_of_Week": {"dtype": "int8", "source_tag": "derived_engineered", "group": "Temporal"},
    "Month": {"dtype": "int8", "source_tag": "derived_engineered", "group": "Temporal"},
    "Quarter": {"dtype": "int8", "source_tag": "derived_engineered", "group": "Temporal"},
    "Is_Weekend": {"dtype": "bool", "source_tag": "derived_engineered", "group": "Temporal"},
    "Is_Holiday": {"dtype": "bool", "source_tag": "real_api", "group": "Temporal"},
    "Festival_Name": {"dtype": "string", "source_tag": "real_api", "group": "Temporal"},
    "Days_Until_Next_Festival": {"dtype": "int16", "source_tag": "derived_engineered", "group": "Temporal"},
    "Is_Month_End": {"dtype": "bool", "source_tag": "derived_engineered", "group": "Temporal"},
    "Days_Since_Launch": {"dtype": "int16", "source_tag": "derived_engineered", "group": "Temporal"},
    "Days_Since_Last_Price_Change": {"dtype": "int16", "source_tag": "derived_engineered", "group": "Temporal"},

    # Group 3 — Pricing & Cost (8 columns)
    "MRP": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Pricing & Cost"},
    "Cost_Price": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Pricing & Cost"},
    "Current_Price": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Pricing & Cost"},
    "Discount_Pct": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Pricing & Cost"},
    "Margin_Pct": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Pricing & Cost"},
    "Min_Allowed_Price": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Pricing & Cost"},
    "Max_Allowed_Price": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Pricing & Cost"},
    "Marketplace_Fee_Pct": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Pricing & Cost"},

    # Group 4 — Inventory (6 columns)
    "Stock_Level": {"dtype": "int32", "source_tag": "simulated_documented", "group": "Inventory"},
    "Reorder_Point": {"dtype": "int32", "source_tag": "simulated_documented", "group": "Inventory"},
    "Lead_Time_Days": {"dtype": "int16", "source_tag": "simulated_documented", "group": "Inventory"},
    "Stock_Out_Risk": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Inventory"},
    "Warehouse_ID": {"dtype": "string", "source_tag": "simulated_documented", "group": "Inventory"},
    "Restock_Cost": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Inventory"},

    # Group 5 — Weather (5 columns)
    "Temperature": {"dtype": "float32", "source_tag": "real_api", "group": "Weather"},
    "Humidity": {"dtype": "float32", "source_tag": "real_api", "group": "Weather"},
    "Rainfall": {"dtype": "float32", "source_tag": "real_api", "group": "Weather"},
    "Weather_Type": {"dtype": "string", "source_tag": "real_api", "group": "Weather"},
    "Is_Extreme_Weather": {"dtype": "bool", "source_tag": "derived_engineered", "group": "Weather"},

    # Group 6 — Macroeconomics (5 columns)
    "USD_INR": {"dtype": "float32", "source_tag": "real_api", "group": "Macroeconomics"},
    "Crude_Oil_Price_USD": {"dtype": "float32", "source_tag": "real_api", "group": "Macroeconomics"},
    "Gold_Price": {"dtype": "float32", "source_tag": "real_api", "group": "Macroeconomics"},
    "Inflation_Index": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Macroeconomics"},
    "Consumer_Confidence_Proxy": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Macroeconomics"},

    # Group 7 — Competitor Intelligence (6 columns)
    "Competitor_Avg_Price": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Competitor Intelligence"},
    "Competitor_Min_Price": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Competitor Intelligence"},
    "Price_Gap_Pct": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Competitor Intelligence"},
    "Competitor_Stock_Status": {"dtype": "string", "source_tag": "simulated_documented", "group": "Competitor Intelligence"},
    "Competitor_Discount_Pct": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Competitor Intelligence"},
    "Market_Rank": {"dtype": "int8", "source_tag": "simulated_documented", "group": "Competitor Intelligence"},

    # Group 8 — Demand Signals (8 columns)
    "Views": {"dtype": "int32", "source_tag": "simulated_documented", "group": "Demand Signals"},
    "Clicks": {"dtype": "int32", "source_tag": "simulated_documented", "group": "Demand Signals"},
    "Cart_Adds": {"dtype": "int32", "source_tag": "simulated_documented", "group": "Demand Signals"},
    "Orders": {"dtype": "int32", "source_tag": "simulated_documented", "group": "Demand Signals"},
    "Conversion_Rate": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Demand Signals"},
    "Search_Trend_Index": {"dtype": "float32", "source_tag": "real_api", "group": "Demand Signals"},
    "Demand_Index": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Demand Signals"},
    "Return_Rate": {"dtype": "float32", "source_tag": "simulated_documented", "group": "Demand Signals"},

    # Group 9 — Engineered / AI Features (8 columns)
    "Price_Lag_7": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},
    "Demand_Lag_7": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},
    "Rolling_Avg_Price_30d": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},
    "Price_Elasticity_Score": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},
    "Seasonality_Impact_Score": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},
    "Festival_Impact_Score": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},
    "Weather_Impact_Score": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},
    "Price_Volatility_30d": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Engineered Features"},

    # Group 10 — AI-Suggested Extra Columns (6 columns)
    "Price_to_Competitor_Ratio": {"dtype": "float32", "source_tag": "derived_engineered", "group": "AI-Suggested Features"},
    "Stock_Days_Remaining": {"dtype": "float32", "source_tag": "derived_engineered", "group": "AI-Suggested Features"},
    "Demand_Momentum_7d": {"dtype": "float32", "source_tag": "derived_engineered", "group": "AI-Suggested Features"},
    "Revenue_Per_Unit": {"dtype": "float32", "source_tag": "derived_engineered", "group": "AI-Suggested Features"},
    "Price_Rank_in_Category": {"dtype": "int8", "source_tag": "derived_engineered", "group": "AI-Suggested Features"},
    "Fuel_Price_INR_Proxy": {"dtype": "float32", "source_tag": "derived_engineered", "group": "AI-Suggested Features"},

    # Group 11 — Target (1 column)
    "Optimal_Price": {"dtype": "float32", "source_tag": "derived_engineered", "group": "Target"}
}

ALL_COLUMNS = list(COLUMN_SCHEMA.keys())
assert len(ALL_COLUMNS) == 71, f"Expected 71 columns, got {len(ALL_COLUMNS)}"
