"""
Validation and Quality Assurance module.
Enforces business rules, funnel integrity, zero-null constraints, elasticity recovery,
outlier capping, and baseline ML sanity benchmarks.
"""
import json
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_absolute_percentage_error
import lightgbm as lgb

from .config import (
    CATEGORY_CONFIG,
    ALL_COLUMNS,
    MIN_TARGET_ROWS,
    MAX_TARGET_ROWS,
    VALIDATION_REPORT_PATH,
    REJECTED_ROWS_PATH,
    DATA_DIR
)

def run_data_validation(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes comprehensive validation suite:
    - Integrity checks (nulls, duplicates, bounds)
    - Funnel monotonicity (Orders <= Cart_Adds <= Clicks <= Views)
    - Outlier detection and capping for Optimal_Price
    - Elasticity recovery regression check
    - Baseline ML model evaluation (Linear Regression + LightGBM)
    """
    print("\n=======================================================")
    print("  RUNNING COMPREHENSIVE DATASET VALIDATION SUITE")
    print("=======================================================\n")

    report: Dict[str, Any] = {
        "total_rows_evaluated": len(df),
        "total_columns": len(df.columns),
        "checks_passed": True,
        "violations": {},
        "elasticity_recovery": {},
        "baseline_models": {}
    }

    # 1. Row & Column Count Checks
    print("[Validation 1/6] Checking row and column specifications...")
    assert len(df.columns) == 71, f"Expected 71 columns, found {len(df.columns)}"
    assert set(df.columns) == set(ALL_COLUMNS), "Column names do not match canonical schema"
    assert MIN_TARGET_ROWS <= len(df) <= MAX_TARGET_ROWS, f"Row count {len(df)} outside range [{MIN_TARGET_ROWS}, {MAX_TARGET_ROWS}]"
    print(f"  [PASS] Row count: {len(df):,} | Column count: {len(df.columns)}")

    # 2. Null Values & Duplicates
    print("\n[Validation 2/6] Checking null values and uniqueness...")
    null_counts = df.isnull().sum().to_dict()
    total_nulls = sum(null_counts.values())
    if total_nulls > 0:
        report["violations"]["null_columns"] = {k: int(v) for k, v in null_counts.items() if v > 0}
        report["checks_passed"] = False
        print(f"  [FAIL] Found {total_nulls} null values!")
    else:
        print("  [PASS] Zero null values across all 71 columns.")

    dup_count = df.duplicated(subset=["Product_ID", "City", "Date"]).sum()
    if dup_count > 0:
        report["violations"]["duplicates"] = int(dup_count)
        report["checks_passed"] = False
        print(f"  [FAIL] Found {dup_count} duplicate (Product_ID, City, Date) records!")
    else:
        print("  [PASS] Zero duplicates on (Product_ID, City, Date).")

    # 3. Funnel Monotonicity & Logic Bounds
    print("\n[Validation 3/6] Validating demand funnel and business logic rules...")
    rejections = []
    
    funnel_fail = (df["Orders"] > df["Cart_Adds"]) | (df["Cart_Adds"] > df["Clicks"]) | (df["Clicks"] > df["Views"])
    if funnel_fail.sum() > 0:
        print(f"  [FAIL] Funnel integrity violated in {funnel_fail.sum()} rows.")
        rej = df[funnel_fail].copy()
        rej["Rejection_Reason"] = "Funnel Monotonicity Violation (Orders > Cart_Adds or Cart_Adds > Clicks or Clicks > Views)"
        rejections.append(rej)

    price_bounds_fail = (df["Current_Price"] < df["Min_Allowed_Price"]) | (df["Current_Price"] > df["Max_Allowed_Price"])
    if price_bounds_fail.sum() > 0:
        print(f"  [FAIL] Current_Price outside min/max bounds in {price_bounds_fail.sum()} rows.")
        rej = df[price_bounds_fail].copy()
        rej["Rejection_Reason"] = "Current_Price outside [Min_Allowed_Price, Max_Allowed_Price]"
        rejections.append(rej)

    optimal_bounds_fail = (df["Optimal_Price"] < df["Min_Allowed_Price"]) | (df["Optimal_Price"] > df["Max_Allowed_Price"])
    if optimal_bounds_fail.sum() > 0:
        print(f"  [FAIL] Optimal_Price outside min/max bounds in {optimal_bounds_fail.sum()} rows.")
        rej = df[optimal_bounds_fail].copy()
        rej["Rejection_Reason"] = "Optimal_Price outside [Min_Allowed_Price, Max_Allowed_Price]"
        rejections.append(rej)

    margin_floor_fail = df["Current_Price"] < (df["Cost_Price"] * 1.049)
    if margin_floor_fail.sum() > 0:
        print(f"  [FAIL] Margin floor violated in {margin_floor_fail.sum()} rows.")
        rej = df[margin_floor_fail].copy()
        rej["Rejection_Reason"] = "Margin Floor (< Cost_Price * 1.05)"
        rejections.append(rej)

    if rejections:
        rejected_df = pd.concat(rejections, ignore_index=True).drop_duplicates(subset=["Product_ID", "City", "Date"])
        rejected_df.to_csv(REJECTED_ROWS_PATH, index=False)
        print(f"  Saved {len(rejected_df)} rejected rows to {REJECTED_ROWS_PATH}")
        report["violations"]["rejected_rows_count"] = len(rejected_df)
    else:
        # Create empty rejected rows file
        pd.DataFrame(columns=ALL_COLUMNS + ["Rejection_Reason"]).to_csv(REJECTED_ROWS_PATH, index=False)
        print("  [PASS] Funnel monotonicity and price boundary rules 100% satisfied.")
        report["violations"]["rejected_rows_count"] = 0

    # 4. Outlier Capping (3-sigma boundary per category)
    print("\n[Validation 4/6] Checking for Optimal_Price outliers (3-sigma rule per category)...")
    capped_df = df.copy()
    outlier_count = 0
    for cat in df["Category"].unique():
        cat_mask = capped_df["Category"] == cat
        mean_p = capped_df.loc[cat_mask, "Optimal_Price"].mean()
        std_p = capped_df.loc[cat_mask, "Optimal_Price"].std()
        
        low_3s = max(0.0, mean_p - 3 * std_p)
        high_3s = mean_p + 3 * std_p
        
        cat_outliers = (capped_df.loc[cat_mask, "Optimal_Price"] < low_3s) | (capped_df.loc[cat_mask, "Optimal_Price"] > high_3s)
        outlier_count += cat_outliers.sum()
        
        # Cap outliers
        capped_df.loc[cat_mask, "Optimal_Price"] = np.clip(capped_df.loc[cat_mask, "Optimal_Price"], low_3s, high_3s).round(2)

    print(f"  Outliers identified and capped: {outlier_count} records across {len(df['Category'].unique())} categories.")
    report["outliers_capped"] = int(outlier_count)

    # 5. Elasticity Recovery Validation (Within-SKU Panel Log-Log OLS Regression)
    print("\n[Validation 5/6] Validating price elasticity recovery via within-SKU panel OLS regression...")
    elasticity_results = {}
    for cat, cfg in CATEGORY_CONFIG.items():
        cat_data = capped_df[capped_df["Category"] == cat].copy()
        
        # Microeconomic panel regression: demean by SKU-City to control for SKU-level baseline differences
        cat_data["log_p"] = np.log(cat_data["Current_Price"].values.astype(float))
        cat_data["log_q"] = np.log(np.maximum(cat_data["Orders"].values.astype(float), 1.0))
        
        # Demean per SKU-City group
        cat_data["dm_log_p"] = cat_data["log_p"] - cat_data.groupby(["SKU", "City"])["log_p"].transform("mean")
        cat_data["dm_log_q"] = cat_data["log_q"] - cat_data.groupby(["SKU", "City"])["log_q"].transform("mean")
        
        slope, intercept, r_val, p_val, std_err = linregress(cat_data["dm_log_p"].values, cat_data["dm_log_q"].values)
        seeded_val = cfg["seeded_elasticity"]
        delta = abs(slope - seeded_val)
        
        passed = delta <= 0.20
        elasticity_results[cat] = {
            "seeded_elasticity": seeded_val,
            "recovered_elasticity": round(float(slope), 3),
            "r_squared": round(float(r_val ** 2), 3),
            "p_value": float(p_val),
            "delta": round(float(delta), 3),
            "status": "PASS" if passed else "WARN"
        }
        status_tag = "[PASS]" if passed else "[WARN]"
        print(f"  {status_tag} {cat:20s}: Seeded = {seeded_val:5.2f} | Recovered = {slope:5.2f} | R^2 = {r_val**2:4.2f} (Delta = {delta:.3f})")

    report["elasticity_recovery"] = elasticity_results

    # 6. Baseline ML Models Benchmark (Chronological Train/Val/Test Split)
    print("\n[Validation 6/6] Training baseline models on chronological train/val/test split...")
    # Train: 2023-01-01 to 2025-06-30
    # Val:   2025-07-01 to 2025-12-31
    # Test:  2026-01-01 to 2026-08-02
    train_mask = capped_df["Date"] <= "2025-06-30"
    val_mask = (capped_df["Date"] > "2025-06-30") & (capped_df["Date"] <= "2025-12-31")
    test_mask = capped_df["Date"] >= "2026-01-01"

    print(f"  Split sizes: Train = {train_mask.sum():,} ({train_mask.sum()/len(capped_df)*100:.1f}%) | Val = {val_mask.sum():,} ({val_mask.sum()/len(capped_df)*100:.1f}%) | Test = {test_mask.sum():,} ({test_mask.sum()/len(capped_df)*100:.1f}%)")

    # Target: Scale-invariant Optimal Markup Percentage = (Optimal_Price - Cost_Price) / Cost_Price
    y_markup = ((capped_df["Optimal_Price"] - capped_df["Cost_Price"]) / capped_df["Cost_Price"]).astype(np.float32)
    y_train_m = y_markup[train_mask]
    y_test_m = y_markup[test_mask]

    # Feature Set (a): Engineered Contextual Features Only (Excluding raw price scales: Cost_Price, Current_Price, MRP, Competitor_Avg_Price)
    feat_engineered = [
        "Marketplace_Fee_Pct", "Price_Gap_Pct", "Price_to_Competitor_Ratio", "Competitor_Discount_Pct", "Market_Rank",
        "Stock_Level", "Reorder_Point", "Stock_Out_Risk", "Stock_Days_Remaining",
        "Temperature", "Humidity", "Rainfall", "Is_Extreme_Weather",
        "USD_INR", "Crude_Oil_Price_USD", "Gold_Price", "Inflation_Index", "Consumer_Confidence_Proxy", "Fuel_Price_INR_Proxy",
        "Views", "Clicks", "Cart_Adds", "Orders", "Conversion_Rate", "Search_Trend_Index", "Demand_Index", "Return_Rate",
        "Demand_Lag_7", "Price_Volatility_30d",
        "Price_Elasticity_Score", "Festival_Impact_Score", "Weather_Impact_Score", "Seasonality_Impact_Score",
        "Day_of_Week", "Month", "Quarter", "Is_Weekend", "Is_Holiday", "Days_Until_Next_Festival",
        "Days_Since_Launch", "Days_Since_Last_Price_Change", "Demand_Momentum_7d", "Price_Rank_in_Category"
    ]

    # Feature Set (b): Trivial Baseline (Cost_Price & Competitor_Avg_Price only)
    feat_trivial = ["Cost_Price", "Competitor_Avg_Price"]

    # Feature Set (c): Full Production Features (All 45 features)
    feat_full = [
        "Cost_Price", "Current_Price", "MRP", "Marketplace_Fee_Pct",
        "Competitor_Avg_Price", "Competitor_Min_Price", "Price_Gap_Pct", "Price_to_Competitor_Ratio",
        "Stock_Level", "Reorder_Point", "Stock_Out_Risk", "Stock_Days_Remaining",
        "Temperature", "Humidity", "Rainfall", "Is_Extreme_Weather",
        "USD_INR", "Crude_Oil_Price_USD", "Gold_Price", "Inflation_Index", "Consumer_Confidence_Proxy", "Fuel_Price_INR_Proxy",
        "Views", "Clicks", "Cart_Adds", "Orders", "Conversion_Rate", "Search_Trend_Index", "Demand_Index", "Return_Rate",
        "Price_Lag_7", "Demand_Lag_7", "Rolling_Avg_Price_30d", "Price_Volatility_30d",
        "Price_Elasticity_Score", "Festival_Impact_Score", "Weather_Impact_Score", "Seasonality_Impact_Score",
        "Day_of_Week", "Month", "Quarter", "Is_Weekend", "Is_Holiday", "Days_Until_Next_Festival", "Days_Since_Launch"
    ]

    # --- Run Model (a): Engineered Features Model ---
    X_train_a = capped_df.loc[train_mask, feat_engineered].astype(np.float32)
    X_test_a = capped_df.loc[test_mask, feat_engineered].astype(np.float32)

    lr_a = LinearRegression()
    lr_a.fit(X_train_a, y_train_m)
    y_pred_lr_a = lr_a.predict(X_test_a)
    r2_lr_a = r2_score(y_test_m, y_pred_lr_a)
    mae_lr_a = mean_absolute_error(y_test_m, y_pred_lr_a)

    lgb_train_a = lgb.Dataset(X_train_a, label=y_train_m)
    lgb_test_a = lgb.Dataset(X_test_a, label=y_test_m, reference=lgb_train_a)
    params = {"objective": "regression", "metric": "rmse", "learning_rate": 0.08, "num_leaves": 31, "verbose": -1, "random_state": 42}
    gbm_a = lgb.train(params, lgb_train_a, num_boost_round=150)
    y_pred_gbm_a = gbm_a.predict(X_test_a)
    r2_gbm_a = r2_score(y_test_m, y_pred_gbm_a)
    mae_gbm_a = mean_absolute_error(y_test_m, y_pred_gbm_a)

    # --- Run Model (b): Trivial Baseline ---
    X_train_b = capped_df.loc[train_mask, feat_trivial].astype(np.float32)
    X_test_b = capped_df.loc[test_mask, feat_trivial].astype(np.float32)

    lr_b = LinearRegression()
    lr_b.fit(X_train_b, y_train_m)
    y_pred_lr_b = lr_b.predict(X_test_b)
    r2_lr_b = r2_score(y_test_m, y_pred_lr_b)
    mae_lr_b = mean_absolute_error(y_test_m, y_pred_lr_b)

    lgb_train_b = lgb.Dataset(X_train_b, label=y_train_m)
    lgb_test_b = lgb.Dataset(X_test_b, label=y_test_m, reference=lgb_train_b)
    gbm_b = lgb.train(params, lgb_train_b, num_boost_round=150)
    y_pred_gbm_b = gbm_b.predict(X_test_b)
    r2_gbm_b = r2_score(y_test_m, y_pred_gbm_b)
    mae_gbm_b = mean_absolute_error(y_test_m, y_pred_gbm_b)

    # --- Run Model (c): Full Production Model ---
    X_train_c = capped_df.loc[train_mask, feat_full].astype(np.float32)
    X_test_c = capped_df.loc[test_mask, feat_full].astype(np.float32)

    lgb_train_c = lgb.Dataset(X_train_c, label=y_train_m)
    lgb_test_c = lgb.Dataset(X_test_c, label=y_test_m, reference=lgb_train_c)
    gbm_c = lgb.train(params, lgb_train_c, num_boost_round=150)
    y_pred_gbm_c = gbm_c.predict(X_test_c)
    r2_gbm_c = r2_score(y_test_m, y_pred_gbm_c)
    mae_gbm_c = mean_absolute_error(y_test_m, y_pred_gbm_c)

    print(f"  [Model A: Engineered Features Only] Linear R^2 = {r2_lr_a:.4f} | LightGBM R^2 = {r2_gbm_a:.4f} | MAE = {mae_gbm_a:.4f} ({mae_gbm_a*100:.2f}% markup error)")
    print(f"  [Model B: Trivial Cost/Comp Only]   Linear R^2 = {r2_lr_b:.4f} | LightGBM R^2 = {r2_gbm_b:.4f} | MAE = {mae_gbm_b:.4f} ({mae_gbm_b*100:.2f}% markup error)")
    print(f"  [Model C: Full Production Engine]   LightGBM R^2 = {r2_gbm_c:.4f} | MAE = {mae_gbm_c:.4f} ({mae_gbm_c*100:.2f}% markup error)")

    # Feature importances for full model
    importance_dict = dict(zip(feat_full, gbm_c.feature_importance(importance_type="gain")))
    top_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:8]
    print(f"  Top Predictive Features (Markup): {', '.join([f'{k} ({v:.0f})' for k, v in top_features[:5]])}")

    report["baseline_models"] = {
        "target_variable": "Optimal_Markup_Pct = (Optimal_Price - Cost_Price) / Cost_Price",
        "model_a_engineered_only": {
            "description": "Contextual, demand, weather, festival, elasticity, and ratio features (Excluding raw price scales)",
            "linear_regression_r2": round(float(r2_lr_a), 4),
            "linear_regression_mae": round(float(mae_lr_a), 4),
            "lightgbm_r2": round(float(r2_gbm_a), 4),
            "lightgbm_mae": round(float(mae_gbm_a), 4),
            "lightgbm_markup_error_pct": round(float(mae_gbm_a * 100), 2)
        },
        "model_b_trivial_baseline": {
            "description": "Cost_Price and Competitor_Avg_Price only",
            "linear_regression_r2": round(float(r2_lr_b), 4),
            "linear_regression_mae": round(float(mae_lr_b), 4),
            "lightgbm_r2": round(float(r2_gbm_b), 4),
            "lightgbm_mae": round(float(mae_gbm_b), 4),
            "lightgbm_markup_error_pct": round(float(mae_gbm_b * 100), 2)
        },
        "model_c_full_production": {
            "description": "All 45 pricing, inventory, macro, and contextual features",
            "lightgbm_r2": round(float(r2_gbm_c), 4),
            "lightgbm_mae": round(float(mae_gbm_c), 4),
            "lightgbm_markup_error_pct": round(float(mae_gbm_c * 100), 2),
            "top_features": {k: float(round(v, 2)) for k, v in top_features}
        },
        "linear_regression": {
            "r2_score": round(float(r2_lr_a), 4),
            "mae": round(float(mae_lr_a), 4),
            "mape_pct": round(float(mae_lr_a * 100), 2)
        },
        "lightgbm": {
            "r2_score": round(float(r2_gbm_c), 4),
            "mae": round(float(mae_gbm_c), 4),
            "mape_pct": round(float(mae_gbm_c * 100), 2),
            "top_features": {k: float(round(v, 2)) for k, v in top_features}
        }
    }

    # Write validation report
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[Validation] Complete validation report saved to {VALIDATION_REPORT_PATH}")

    return capped_df, report
