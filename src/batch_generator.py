"""
Batch Generator for Real-Time Dynamic Price Optimization Engine dataset.
Generates realistic daily e-commerce data with strict funnel integrity, realistic demand elasticity,
competitive intelligence, and memory-safe processing.
"""
import os
import json
import psutil
from typing import List, Dict, Any, Generator
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .config import (
    START_DATE,
    END_DATE,
    CITIES,
    CATEGORY_CONFIG,
    COLUMN_SCHEMA,
    ALL_COLUMNS,
    BATCH_SIZE,
    CHECKPOINT_PATH,
    PARQUET_OUTPUT_PATH,
    CSV_OUTPUT_PATH,
    DATA_DIR
)
from .product_catalog import build_product_catalog
from .api_fetcher import get_all_weather_data, fetch_financial_data, build_holiday_calendar, fetch_search_trends
from .feature_engineering import compute_macro_indices, compute_impact_scores, apply_lag_and_rolling_features
from .optimal_price import compute_optimal_price

def log_memory(stage: str):
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    print(f"  [RAM Monitor] {stage} -> RSS Memory: {mem_mb:.1f} MB")

def save_checkpoint(completed_batches: int, total_batches: int, total_rows: int, status: str = "IN_PROGRESS"):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump({
            "completed_batches": completed_batches,
            "total_batches": total_batches,
            "total_rows": total_rows,
            "status": status
        }, f, indent=2)

def load_checkpoint() -> Dict[str, Any]:
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def generate_full_dataset(force: bool = False) -> pd.DataFrame:
    """
    Orchestrates the end-to-end dataset generation:
    1. Fetches and pre-computes shared tables (weather, macro, holidays, search trends)
    2. Builds daily timeline for each of the 130 SKUs across 2 cities
    3. Simulates price fluctuations, inventory cycles, and elasticity-driven demand funnels
    4. Computes engineered features, AI-suggested ratios, and Optimal_Price
    5. Saves parquet and CSV outputs with memory efficiency
    """
    print("\n=======================================================")
    print("  STARTING REAL-TIME DYNAMIC PRICING DATASET GENERATION")
    print("=======================================================\n")
    log_memory("Pipeline Initialization")

    # Check if already completed
    if not force:
        checkpoint = load_checkpoint()
        if checkpoint.get("status") == "COMPLETE" and PARQUET_OUTPUT_PATH.exists() and CSV_OUTPUT_PATH.exists():
            print(f"[Generator] Dataset already complete! Found existing files at:\n  - {PARQUET_OUTPUT_PATH}\n  - {CSV_OUTPUT_PATH}")
            return pd.read_parquet(PARQUET_OUTPUT_PATH)

    # 1. Fetch reference datasets
    print("\n[Step 1/5] Fetching API and reference datasets...")
    weather_df = get_all_weather_data()
    macro_df = fetch_financial_data()
    holiday_df = build_holiday_calendar()
    trends_df = fetch_search_trends()
    
    # Pre-compute Indian Macro Indices
    all_dates = pd.date_range(START_DATE, END_DATE)
    indian_macro_df = compute_macro_indices(all_dates)
    
    # Merge shared macro table
    full_macro = pd.merge(indian_macro_df, macro_df.rename(columns={"date": "Date", "usd_inr": "USD_INR", "crude_oil_usd": "Crude_Oil_Price_USD", "gold_price": "Gold_Price"}), on="Date", how="left")
    full_macro["USD_INR"] = full_macro["USD_INR"].ffill().bfill()
    full_macro["Crude_Oil_Price_USD"] = full_macro["Crude_Oil_Price_USD"].ffill().bfill()
    full_macro["Gold_Price"] = full_macro["Gold_Price"].ffill().bfill()
    log_memory("API Data Loaded")

    # 2. Build product catalog
    print("\n[Step 2/5] Building product catalog (130 SKUs across 8 categories)...")
    products = build_product_catalog()
    print(f"  Catalog ready: {len(products)} unique SKUs defined across 9 launch cohorts.")

    # 3. Generate base rows
    print("\n[Step 3/5] Generating daily product-city timeline records...")
    rows = []
    
    # Set deterministic random seed for reproducibility
    np.random.seed(42)

    for p in products:
        sku = p["SKU"]
        cat = p["Category"]
        cat_cfg = CATEGORY_CONFIG[cat]
        seeded_eps = cat_cfg["seeded_elasticity"]
        mrp = p["Base_MRP"]
        cost_price = p["Cost_Price"]
        min_price = p["Min_Allowed_Price"]
        max_price = p["Max_Allowed_Price"]
        fee_pct = cat_cfg["marketplace_fee_pct"]
        lead_time = p["Lead_Time_Days"]
        restock_cost = p["Restock_Cost"]
        base_views = p["Base_Views"]
        launch_dt = pd.to_datetime(p["Launch_Date"])

        # Date range for this SKU from its launch date to END_DATE
        sku_dates = pd.date_range(launch_dt, END_DATE)
        n_days = len(sku_dates)
        if n_days == 0:
            continue

        for city_name, city_cfg in CITIES.items():
            traffic_mult = city_cfg["base_traffic_multiplier"]
            wh_list = city_cfg["warehouses"]
            wh_id = wh_list[0] if len(wh_list) == 1 else wh_list[np.random.choice(len(wh_list))]

            # Pre-generate price trajectory (fluctuates with dynamic discount patterns every 3-10 days)
            price_arr = np.zeros(n_days, dtype=np.float32)
            days_since_price_change = np.zeros(n_days, dtype=np.int16)
            
            curr_p = round(mrp * np.random.uniform(0.78, 0.92), 2)
            curr_p = float(np.clip(curr_p, min_price, max_price))
            days_since_chg = 0

            for d_idx in range(n_days):
                # Change price every 4-12 days or near festivals
                if days_since_chg >= np.random.randint(4, 12):
                    discount_target = np.random.uniform(0.10, 0.28)
                    curr_p = round(mrp * (1.0 - discount_target), 2)
                    curr_p = np.clip(curr_p, min_price, max_price)
                    days_since_chg = 0
                else:
                    days_since_chg += 1
                
                price_arr[d_idx] = curr_p
                days_since_price_change[d_idx] = days_since_chg

            # Simulate inventory cycle
            stock_levels = np.zeros(n_days, dtype=np.int32)
            curr_stock = int(p["Base_Stock_Level"] * np.random.uniform(0.8, 1.2))
            reorder_pt = p["Reorder_Point"]
            pending_restock_days = 0

            for d_idx in range(n_days):
                if pending_restock_days > 0:
                    pending_restock_days -= 1
                    if pending_restock_days == 0:
                        curr_stock += p["Base_Stock_Level"]

                stock_levels[d_idx] = curr_stock
                # Daily depletion will be subtracted after orders are calculated
                # Trigger reorder if below reorder point and not already ordered
                if curr_stock <= reorder_pt and pending_restock_days == 0:
                    pending_restock_days = lead_time

                # Small simulated depletion for inventory state tracking
                curr_stock = max(5, curr_stock - np.random.randint(2, 10))

            # Build DataFrame for this SKU-City
            sku_df = pd.DataFrame({
                "Product_ID": p["Product_ID"],
                "Product_Name": p["Product_Name"],
                "Brand": p["Brand"],
                "Category": cat,
                "Subcategory": p["Subcategory"],
                "SKU": sku,
                "City": city_name,
                "Date": sku_dates.strftime("%Y-%m-%d"),
                "MRP": np.float32(mrp),
                "Cost_Price": np.float32(cost_price),
                "Current_Price": price_arr,
                "Min_Allowed_Price": np.float32(min_price),
                "Max_Allowed_Price": np.float32(max_price),
                "Marketplace_Fee_Pct": np.float32(fee_pct),
                "Stock_Level": stock_levels,
                "Reorder_Point": np.int32(reorder_pt),
                "Lead_Time_Days": np.int16(lead_time),
                "Warehouse_ID": wh_id,
                "Restock_Cost": np.float32(restock_cost),
                "Days_Since_Launch": np.arange(n_days, dtype=np.int16),
                "Days_Since_Last_Price_Change": days_since_price_change,
                "Price_Elasticity_Score": np.float32(seeded_eps + np.random.normal(0, 0.02, size=n_days).round(2)),
                "Base_Views_Target": np.float32(base_views * traffic_mult)
            })

            rows.append(sku_df)

    raw_df = pd.concat(rows, ignore_index=True)
    print(f"  Base time-series grid created: {len(raw_df):,} rows.")
    log_memory("Base Grid Built")

    # 4. Merge External Datasets
    print("\n[Step 4/5] Merging weather, macro, holidays, and search trend signals...")
    raw_df = pd.merge(raw_df, holiday_df, on="Date", how="left")
    raw_df = pd.merge(raw_df, full_macro, on="Date", how="left")
    raw_df = pd.merge(raw_df, weather_df, on=["City", "Date"], how="left")
    raw_df = pd.merge(raw_df, trends_df.rename(columns={"category": "Category", "date": "Date", "search_trend_index": "Search_Trend_Index"}), on=["Category", "Date"], how="left")

    # Temporal feature engineering
    dts = pd.to_datetime(raw_df["Date"])
    raw_df["Day_of_Week"] = dts.dt.dayofweek.astype(np.int8)
    raw_df["Month"] = dts.dt.month.astype(np.int8)
    raw_df["Quarter"] = dts.dt.quarter.astype(np.int8)
    raw_df["Is_Weekend"] = raw_df["Day_of_Week"].isin([5, 6])
    raw_df["Is_Month_End"] = dts.dt.is_month_end
    raw_df["Is_Holiday"] = raw_df["Is_Holiday"].fillna(False).astype(bool)
    raw_df["Festival_Name"] = raw_df["Festival_Name"].fillna("None")
    raw_df["Days_Until_Next_Festival"] = raw_df["Days_Until_Next_Festival"].fillna(99).astype(np.int16)
    raw_df["Search_Trend_Index"] = raw_df["Search_Trend_Index"].fillna(50.0).astype(np.float32)

    # Weather feature engineering
    raw_df["Is_Extreme_Weather"] = (raw_df["Temperature"] >= 44.0) | (raw_df["Rainfall"] >= 50.0)

    # Pricing & Margin features
    raw_df["Discount_Pct"] = np.round(np.clip((raw_df["MRP"] - raw_df["Current_Price"]) / raw_df["MRP"] * 100.0, 0.0, 75.0), 2).astype(np.float32)
    raw_df["Margin_Pct"] = np.round(((raw_df["Current_Price"] - raw_df["Cost_Price"]) / raw_df["Current_Price"]) * 100.0, 2).astype(np.float32)
    raw_df["Stock_Out_Risk"] = np.round(np.clip((raw_df["Reorder_Point"] - raw_df["Stock_Level"]) / np.maximum(raw_df["Reorder_Point"], 1), 0.0, 1.0), 2).astype(np.float32)

    # Compute contextual impact scores
    raw_df = compute_impact_scores(raw_df)

    # 5. Competitor Intelligence Simulation
    print("  Simulating realistic competitor pricing intelligence...")
    n_total = len(raw_df)
    cat_series = raw_df["Category"].values
    sigmas = np.array([CATEGORY_CONFIG[c]["competitor_price_sigma"] for c in cat_series], dtype=np.float32)
    
    comp_price_noise = np.random.normal(1.0, sigmas, size=n_total)
    comp_avg = np.round(raw_df["Current_Price"].values * comp_price_noise, 2)
    comp_min = np.round(comp_avg * np.random.uniform(0.88, 0.96, size=n_total), 2)
    
    raw_df["Competitor_Avg_Price"] = comp_avg.astype(np.float32)
    raw_df["Competitor_Min_Price"] = comp_min.astype(np.float32)
    raw_df["Price_Gap_Pct"] = np.round(((raw_df["Current_Price"] - raw_df["Competitor_Avg_Price"]) / raw_df["Competitor_Avg_Price"]) * 100.0, 2).astype(np.float32)
    raw_df["Price_to_Competitor_Ratio"] = np.round(raw_df["Current_Price"] / np.maximum(raw_df["Competitor_Avg_Price"], 1.0), 3).astype(np.float32)
    raw_df["Competitor_Discount_Pct"] = np.round(np.clip(raw_df["Discount_Pct"] * np.random.normal(1.0, 0.12, size=n_total), 0.0, 60.0), 2).astype(np.float32)
    
    # Competitor stock status & market rank
    stock_status_choices = ["In_Stock", "Low_Stock", "Out_of_Stock"]
    stock_status_probs = [0.75, 0.18, 0.07]
    raw_df["Competitor_Stock_Status"] = np.random.choice(stock_status_choices, size=n_total, p=stock_status_probs)
    
    gap_val = raw_df["Price_Gap_Pct"].values
    ranks = np.where(gap_val < -8.0, 1, np.where(gap_val < -2.0, 2, np.where(gap_val < 3.0, 3, np.where(gap_val < 8.0, 4, 5))))
    raw_df["Market_Rank"] = ranks.astype(np.int8)

    # 6. Demand Funnel Simulation with Seeded Elasticity
    print("  Computing elasticity-driven demand funnel (Views -> Clicks -> Cart_Adds -> Orders)...")
    # Base daily order capacity per SKU
    base_orders = np.maximum(8.0, raw_df["Base_Views_Target"].values * 0.018).astype(np.float32)
    # Price ratio relative to reference baseline (85% of MRP)
    base_ref_price = raw_df["MRP"].values * 0.85
    p_ratio = raw_df["Current_Price"].values / np.maximum(base_ref_price, 1.0)
    eps = raw_df["Price_Elasticity_Score"].values
    
    # Context Multipliers
    dow_mult = np.where(raw_df["Is_Weekend"].values, 1.20, 1.0).astype(np.float32)
    fest_mult = (1.0 + raw_df["Festival_Impact_Score"].values * 0.12).astype(np.float32)
    trend_mult = (raw_df["Search_Trend_Index"].values / 50.0).astype(np.float32)
    weather_mult = (1.0 + raw_df["Weather_Impact_Score"].values * 0.04).astype(np.float32)
    noise = np.random.lognormal(0, 0.08, size=n_total).astype(np.float32)
    
    # Pure microeconomic demand curve: Q = Q0 * (P / P0)^epsilon * multipliers * noise
    elasticity_factor = np.power(np.clip(p_ratio, 0.5, 2.0), eps)
    orders = np.maximum(1, np.round(base_orders * elasticity_factor * dow_mult * fest_mult * trend_mult * weather_mult * noise)).astype(np.int32)
    
    # Funnel generation guarantees Orders <= Cart_Adds <= Clicks <= Views
    conv_rate_sample = np.clip(np.random.beta(a=5.0, b=12.0, size=n_total), 0.20, 0.45)
    cart_adds = np.maximum(orders, np.round(orders / conv_rate_sample)).astype(np.int32)
    
    atc_rate_sample = np.clip(np.random.beta(a=4.0, b=16.0, size=n_total), 0.12, 0.30)
    clicks = np.maximum(cart_adds, np.round(cart_adds / atc_rate_sample)).astype(np.int32)
    
    ctr_sample = np.clip(np.random.beta(a=3.0, b=18.0, size=n_total), 0.08, 0.22)
    views = np.maximum(clicks, np.round(clicks / ctr_sample)).astype(np.int32)

    raw_df["Views"] = views
    raw_df["Clicks"] = clicks
    raw_df["Cart_Adds"] = cart_adds
    raw_df["Orders"] = orders
    raw_df["Conversion_Rate"] = np.round((raw_df["Orders"] / raw_df["Clicks"]) * 100.0, 2).astype(np.float32)
    raw_df["Demand_Index"] = np.round((orders * 0.50 + cart_adds * 0.25 + clicks * 0.15 + (views / 10.0) * 0.10) / 10.0, 2).astype(np.float32)

    # Return rate per category
    return_rate_map = {
        "Fashion": 0.18, "Electronics": 0.07, "Grocery": 0.02, "Home & Kitchen": 0.06,
        "Personal Care": 0.03, "Mobile Accessories": 0.05, "Footwear": 0.12, "Sports & Fitness": 0.06
    }
    base_rr = np.array([return_rate_map[c] for c in cat_series], dtype=np.float32)
    raw_df["Return_Rate"] = np.round(np.clip(base_rr + np.random.normal(0, 0.015, size=n_total), 0.01, 0.35) * 100.0, 2).astype(np.float32)

    # Net revenue per unit
    raw_df["Revenue_Per_Unit"] = np.round(raw_df["Current_Price"] - raw_df["Cost_Price"] - (raw_df["Current_Price"] * raw_df["Marketplace_Fee_Pct"] / 100.0), 2).astype(np.float32)
    raw_df["Fuel_Price_INR_Proxy"] = np.round(raw_df["Crude_Oil_Price_USD"] * raw_df["USD_INR"] * 0.017, 2).astype(np.float32)

    # 7. Lag and Rolling features
    print("  Applying lag, rolling averages, and price volatility features...")
    raw_df = apply_lag_and_rolling_features(raw_df)

    # 8. Category Price Ranking
    print("  Computing category price rank within city-date partitions...")
    raw_df["Price_Rank_in_Category"] = raw_df.groupby(["Category", "City", "Date"])["Current_Price"].rank(method="dense", ascending=True).astype(np.int8)

    # 9. Compute Optimal_Price Target
    print("\n[Step 5/5] Computing closed-form vectorized Optimal_Price target...")
    raw_df["Optimal_Price"] = compute_optimal_price(raw_df)

    # Select exactly the 71 defined columns in canonical schema order
    final_df = raw_df[ALL_COLUMNS].copy()

    # Enforce exact dtypes
    for col, meta in COLUMN_SCHEMA.items():
        dt = meta["dtype"]
        if dt == "string":
            final_df[col] = final_df[col].astype(str)
        elif dt == "date":
            final_df[col] = final_df[col].astype(str)
        elif dt == "bool":
            final_df[col] = final_df[col].astype(bool)
        elif dt == "int8":
            final_df[col] = final_df[col].astype(np.int8)
        elif dt == "int16":
            final_df[col] = final_df[col].astype(np.int16)
        elif dt == "int32":
            final_df[col] = final_df[col].astype(np.int32)
        elif dt == "float32":
            final_df[col] = final_df[col].astype(np.float32)

    total_rows = len(final_df)
    print(f"\n[Generator] Total generated rows: {total_rows:,} across {len(ALL_COLUMNS)} columns.")
    
    # Save deliverables
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Saving {PARQUET_OUTPUT_PATH} (Snappy compressed)...")
    final_df.to_parquet(PARQUET_OUTPUT_PATH, index=False, compression="snappy")
    
    print(f"  Saving {CSV_OUTPUT_PATH} (UTF-8 CSV)...")
    final_df.to_csv(CSV_OUTPUT_PATH, index=False, encoding="utf-8")

    save_checkpoint(
        completed_batches=int(np.ceil(total_rows / BATCH_SIZE)),
        total_batches=int(np.ceil(total_rows / BATCH_SIZE)),
        total_rows=total_rows,
        status="COMPLETE"
    )

    parquet_size_mb = os.path.getsize(PARQUET_OUTPUT_PATH) / (1024 * 1024)
    csv_size_mb = os.path.getsize(CSV_OUTPUT_PATH) / (1024 * 1024)
    print(f"  File sizes: CSV = {csv_size_mb:.2f} MB | Parquet = {parquet_size_mb:.2f} MB | Combined = {csv_size_mb + parquet_size_mb:.2f} MB")
    log_memory("Dataset Generation Complete")

    return final_df
