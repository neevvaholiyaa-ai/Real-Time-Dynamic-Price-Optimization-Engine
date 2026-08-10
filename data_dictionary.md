# Data Dictionary — Real-Time Dynamic Price Optimization Engine

This document provides complete documentation for the 71 columns in the dynamic pricing dataset across Ahmedabad and Surat.

## 1. Schema Overview

- **Total Rows**: ~148,000 daily observations (2023-01-01 to 2026-08-02)
- **Total Columns**: 71 (64 Core + 6 AI-Suggested + 1 Target `Optimal_Price`)
- **Granularity**: Daily per Product SKU and City
- **Cities**: Ahmedabad (23.03° N, 72.58° E) and Surat (21.17° N, 72.83° E)

### Source Provenance Tag Breakdown

| Source Tag | Count | Description |
|---|---|---|
| `real_api` | 10 | Retrieved from live APIs (Open-Meteo, yfinance, Gujarat holidays, pytrends) |
| `simulated_documented` | 24 | Scientifically simulated market signals using established economic models |
| `derived_engineered` | 37 | Computed transformations, time features, lag/rolling features, and target price |

---

## 2. Complete Column Specifications

| # | Column Name | Dtype | Source Tag | Group | Description & Formula / Provenance |
|---|---|---|---|---|---|
| 1 | `Product_ID` | string | simulated_documented | Identifiers | Unique master identifier for product (e.g. `PROD-ELEC-001`) |
| 2 | `Product_Name` | string | simulated_documented | Identifiers | Commercial product title |
| 3 | `Brand` | string | simulated_documented | Identifiers | Brand name (e.g. `SoundPulse`, `RangGujarat`) |
| 4 | `Category` | string | simulated_documented | Identifiers | 1 of 8 primary ecommerce retail categories |
| 5 | `Subcategory` | string | simulated_documented | Identifiers | Granular sub-department (e.g. `Audio`, `Cookware`) |
| 6 | `SKU` | string | simulated_documented | Identifiers | Stock Keeping Unit code (e.g. `SKU-ELEC-001`) |
| 7 | `City` | string | simulated_documented | Identifiers | Retail fulfillment city: `Ahmedabad` or `Surat` |
| 8 | `Date` | date | simulated_documented | Identifiers | Observation date (YYYY-MM-DD) |
| 9 | `Day_of_Week` | int8 | derived_engineered | Temporal | Day of week integer (0 = Monday, 6 = Sunday) |
| 10 | `Month` | int8 | derived_engineered | Temporal | Calendar month integer (1 to 12) |
| 11 | `Quarter` | int8 | derived_engineered | Temporal | Calendar quarter (1 to 4) |
| 12 | `Is_Weekend` | bool | derived_engineered | Temporal | Boolean flag for Saturday or Sunday |
| 13 | `Is_Holiday` | bool | real_api | Temporal | Real Gujarat gazetted or major cultural holiday (`holidays.India(prov='GJ')`) |
| 14 | `Festival_Name` | string | real_api | Temporal | Name of holiday or festival (e.g. `Diwali`, `Ahmedabad Rath Yatra`, `Navratri`) |
| 15 | `Days_Until_Next_Festival` | int16 | derived_engineered | Temporal | Count of days until the nearest major cultural festival |
| 16 | `Is_Month_End` | bool | derived_engineered | Temporal | True if observation date is the final day of calendar month |
| 17 | `Days_Since_Launch` | int16 | derived_engineered | Temporal | Days elapsed since SKU launch cohort date |
| 18 | `Days_Since_Last_Price_Change` | int16 | derived_engineered | Temporal | Days elapsed since `Current_Price` was adjusted |
| 19 | `MRP` | float32 | simulated_documented | Pricing & Cost | Maximum Retail Price printed on packaging (INR) |
| 20 | `Cost_Price` | float32 | simulated_documented | Pricing & Cost | Unit acquisition and direct manufacturing cost (INR) |
| 21 | `Current_Price` | float32 | simulated_documented | Pricing & Cost | Active retail selling price on the platform (INR) |
| 22 | `Discount_Pct` | float32 | derived_engineered | Pricing & Cost | `(MRP - Current_Price) / MRP * 100` |
| 23 | `Margin_Pct` | float32 | derived_engineered | Pricing & Cost | `(Current_Price - Cost_Price) / Current_Price * 100` |
| 24 | `Min_Allowed_Price` | float32 | simulated_documented | Pricing & Cost | Guardrail price floor (`Cost_Price * 1.05`) |
| 25 | `Max_Allowed_Price` | float32 | simulated_documented | Pricing & Cost | Guardrail price ceiling (`MRP * 1.05`) |
| 26 | `Marketplace_Fee_Pct` | float32 | simulated_documented | Pricing & Cost | Platform commission and payment processing fee percentage |
| 27 | `Stock_Level` | int32 | simulated_documented | Inventory | Units available in designated city fulfillment warehouse |
| 28 | `Reorder_Point` | int32 | simulated_documented | Inventory | Threshold inventory level that initiates restocking |
| 29 | `Lead_Time_Days` | int16 | simulated_documented | Inventory | Days required for supplier restock fulfillment |
| 30 | `Stock_Out_Risk` | float32 | derived_engineered | Inventory | `clip((Reorder_Point - Stock_Level) / Reorder_Point, 0, 1)` |
| 31 | `Warehouse_ID` | string | simulated_documented | Inventory | Fulfillment hub code (`WH-AMD-01`, `WH-AMD-02`, `WH-SUR-01`) |
| 32 | `Restock_Cost` | float32 | simulated_documented | Inventory | Batch freight and restocking purchase order cost (INR) |
| 33 | `Temperature` | float32 | real_api | Weather | Daily maximum 2m air temperature (°C) from Open-Meteo |
| 34 | `Humidity` | float32 | real_api | Weather | Daily maximum relative humidity (%) from Open-Meteo |
| 35 | `Rainfall` | float32 | real_api | Weather | Daily precipitation sum (mm) from Open-Meteo |
| 36 | `Weather_Type` | string | real_api | Weather | WMO code derived weather condition (`Clear`, `Rainy`, `Thunderstorm`, etc.) |
| 37 | `Is_Extreme_Weather` | bool | derived_engineered | Weather | True if `Temperature >= 44.0°C` or `Rainfall >= 50.0mm` |
| 38 | `USD_INR` | float32 | real_api | Macroeconomics | USD/INR daily exchange rate close (`USDINR=X` via yfinance) |
| 39 | `Crude_Oil_Price_USD` | float32 | real_api | Macroeconomics | WTI Crude Oil futures benchmark in USD/barrel (`CL=F` via yfinance) |
| 40 | `Gold_Price` | float32 | real_api | Macroeconomics | Gold futures in USD/troy oz (`GC=F` via yfinance) |
| 41 | `Inflation_Index` | float32 | simulated_documented | Macroeconomics | Simulated Indian CPI trajectory (base 100, ~5.5% annual RBI band) |
| 42 | `Consumer_Confidence_Proxy` | float32 | simulated_documented | Macroeconomics | Indian consumer sentiment index (scale 35-85, festive peak, monsoon dip) |
| 43 | `Competitor_Avg_Price` | float32 | simulated_documented | Competitor Intelligence | Mean selling price of rival e-commerce platforms (INR) |
| 44 | `Competitor_Min_Price` | float32 | simulated_documented | Competitor Intelligence | Lowest rival marketplace price (INR) |
| 45 | `Price_Gap_Pct` | float32 | derived_engineered | Competitor Intelligence | `(Current_Price - Competitor_Avg_Price) / Competitor_Avg_Price * 100` |
| 46 | `Competitor_Stock_Status` | string | simulated_documented | Competitor Intelligence | Rival inventory availability: `In_Stock`, `Low_Stock`, `Out_of_Stock` |
| 47 | `Competitor_Discount_Pct` | float32 | simulated_documented | Competitor Intelligence | Average discount percentage offered by rival sellers |
| 48 | `Market_Rank` | int8 | simulated_documented | Competitor Intelligence | Price competitiveness rank within category (1 = cheapest, 5 = premium) |
| 49 | `Views` | int32 | simulated_documented | Demand Signals | Product page impressions on marketplace |
| 50 | `Clicks` | int32 | simulated_documented | Demand Signals | Click-through interactions from category and search listings |
| 51 | `Cart_Adds` | int32 | simulated_documented | Demand Signals | Add-to-cart events |
| 52 | `Orders` | int32 | simulated_documented | Demand Signals | Completed purchase orders |
| 53 | `Conversion_Rate` | float32 | derived_engineered | Demand Signals | `(Orders / Clicks) * 100` (%) |
| 54 | `Search_Trend_Index` | float32 | real_api | Demand Signals | Category search volume index scaled 0 to 100 (Google Trends / pytrends) |
| 55 | `Demand_Index` | float32 | derived_engineered | Demand Signals | Weighted funnel score `(Orders*0.5 + Cart_Adds*0.25 + Clicks*0.15 + Views*0.01)` |
| 56 | `Return_Rate` | float32 | simulated_documented | Demand Signals | Historical percentage of orders returned/refunded (%) |
| 57 | `Price_Lag_7` | float32 | derived_engineered | Engineered Features | `Current_Price` 7 days prior for same SKU-City (leakage-free shift) |
| 58 | `Demand_Lag_7` | float32 | derived_engineered | Engineered Features | `Orders` 7 days prior for same SKU-City (leakage-free shift) |
| 59 | `Rolling_Avg_Price_30d` | float32 | derived_engineered | Engineered Features | 30-day backward rolling mean of `Current_Price` |
| 60 | `Price_Elasticity_Score` | float32 | derived_engineered | Engineered Features | Microeconomic price elasticity (Grocery: -1.0, Electronics: -2.2) |
| 61 | `Seasonality_Impact_Score` | float32 | derived_engineered | Engineered Features | Normalized seasonal demand multiplier (-1.5 to +1.5) |
| 62 | `Festival_Impact_Score` | float32 | derived_engineered | Engineered Features | Cultural festival proximity surge multiplier (0.0 to 3.0) |
| 63 | `Weather_Impact_Score` | float32 | derived_engineered | Engineered Features | Category-specific weather impact multiplier (-2.0 to +2.0) |
| 64 | `Price_Volatility_30d` | float32 | derived_engineered | Engineered Features | 30-day standard deviation of historical selling price |
| 65 | `Price_to_Competitor_Ratio` | float32 | derived_engineered | AI-Suggested Features | `Current_Price / Competitor_Avg_Price` (scale-invariant competitor metric) |
| 66 | `Stock_Days_Remaining` | float32 | derived_engineered | AI-Suggested Features | `Stock_Level / Rolling_7d_Orders` (inventory runway in days) |
| 67 | `Demand_Momentum_7d` | float32 | derived_engineered | AI-Suggested Features | Ratio of 7-day moving avg orders to 14-day moving avg orders |
| 68 | `Revenue_Per_Unit` | float32 | derived_engineered | AI-Suggested Features | Net margin `Current_Price - Cost_Price - Marketplace_Fee` (INR) |
| 69 | `Price_Rank_in_Category` | int8 | derived_engineered | AI-Suggested Features | Ascending price rank among SKUs in same Category, City, and Date |
| 70 | `Fuel_Price_INR_Proxy` | float32 | derived_engineered | AI-Suggested Features | `Crude_Oil_Price_USD * USD_INR * 0.017` (estimated retail fuel cost INR/L) |
| 71 | `Optimal_Price` | float32 | derived_engineered | **Target Variable** | Profit-maximizing dynamic optimal price target (INR) |

---

## 3. Mathematical Formulation of Optimal_Price

The target variable `Optimal_Price` is generated using classical microeconomic profit maximization with context adjustment multipliers and bounded safeguards.

### Step 1: Microeconomic Constant-Elasticity Foundation
Given demand function Q(p) = A * p^epsilon, the profit function is:
Pi(p) = (p - c) * Q(p) = (p - c) * A * p^epsilon

Differentiating with respect to p and setting dPi/dp = 0:
p* = c / (1 + 1 / epsilon)

Where effective variable unit cost is:
c = Cost_Price * (1 + Marketplace_Fee_Pct / 100)

### Step 2: Contextual Demand Multipliers
Adjusted_Price = p* * (1 + 0.05 * Festival_Impact_Score) * (1 + 0.02 * Weather_Impact_Score) * (1 + 0.03 * Seasonality_Impact_Score) * competitor_anchor

Where:
competitor_anchor = clip(Competitor_Avg_Price / p*, 0.85, 1.15)

### Step 3: Inventory Urgency
- If Stock_Days_Remaining < 3.0: Multiply by 1.10 (Scarcity pricing)
- If Stock_Days_Remaining > 90.0: Multiply by 0.95 (Markdown clearance)

### Step 4: Safeguard Boundary Clipping
Optimal_Price = clip(Candidate_Price, Lower_Bound, Upper_Bound)
Lower_Bound = max(Min_Allowed_Price, 0.75 * Competitor_Avg_Price, 1.05 * Cost_Price)
Upper_Bound = min(Max_Allowed_Price, 1.25 * Competitor_Avg_Price)
