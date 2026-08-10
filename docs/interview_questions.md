# Technical Interview Guide: Real-Time Dynamic Price Optimization Engine
### Comprehensive Question & Answer Reference for Data Science & ML Engineering Interviews

---

## 1. Problem Formulation & Business Strategy

### Q1: What business problem does this dynamic pricing engine solve?
**Answer:**  
In e-commerce and multi-category retail, static price lists cause two primary points of failure:
1. **Lost Revenue During Demand Surges:** Underpricing when demand is inelastic (such as major festive windows like Navratri/Diwali in Gujarat or sudden weather shifts).
2. **Excess Inventory Carrying Costs:** Overpricing when inventory runway exceeds 60–90 days, tying up working capital.

This engine optimizes the price dynamically for each SKU on a daily basis to maximize gross contribution margin while adhering to strict market competitiveness corridors and profitability floors.

---

### Q2: What is the economic foundation behind the pricing model?
**Answer:**  
The engine is grounded in classical microeconomic **constant-elasticity demand theory**:
$$Q(p) = A \cdot p^\epsilon$$
where $\epsilon < 0$ is the category price elasticity coefficient. For example:
- **Grocery:** Inelastic ($\epsilon \approx -1.0$) — price increases have lower impact on volume.
- **Electronics / Fashion:** Highly elastic ($\epsilon \approx -1.9 \text{ to } -2.2$) — consumers are price-sensitive and compare with competitors.

The unconstrained optimal profit-maximizing markup is:
$$p^* = \text{Cost} \times \left( \frac{\epsilon}{1 + \epsilon + \text{fee}} \right) \times \text{Multiplier}_{\text{context}}$$
The machine learning model learns this non-linear surface across 57 joint market dimensions.

---

## 2. Data Engineering & Integrity

### Q3: How did you validate data quality before feeding it to ML models?
**Answer:**  
We established 6 strict automated validation rules:
1. **Zero Nulls:** Audited across all 71 columns.
2. **Zero Duplicate Keys:** Verified uniqueness on `(Product_ID, City, Date)`.
3. **Funnel Monotonicity:** Enforced e-commerce user behavior logic: $\text{Orders} \le \text{Cart Adds} \le \text{Clicks} \le \text{Views}$.
4. **Profitability Floor:** Guaranteed active selling price $\ge \text{Cost Price} \times 1.05$.
5. **Catalog Boundary Conformance:** Ensured $\text{Min Allowed Price} \le \text{Optimal Price} \le \text{Max Allowed Price}$.
6. **Price Corridor Consistency:** Ensured pricing remains within $[0.75\times, 1.25\times \text{Competitor Avg Price}]$.

---

### Q4: What is the provenance of your dataset?
**Answer:**  
The dataset consists of 145,898 rows across 130 SKUs and 2 metropolitan centers in Gujarat (Ahmedabad and Surat) spanning 2023 to 2026:
- **Real External APIs (10 columns):** Historical weather (Open-Meteo), financial exchange rates & commodities (yfinance: USD/INR, Brent crude, gold), regional Indian holiday schedules (holidays library), and Google search interest (pytrends).
- **Simulated Realistic Operations (24 columns):** Product catalog, inventory stock levels, order funnels, and competitor pricing snapshots.
- **Derived / Engineered Features (37 columns):** Rolling statistics, lag indicators, inventory runway days, and economic impact scores.

---

## 3. Data Leakage & Feature Engineering

### Q5: How did you partition the dataset to avoid data leakage?
**Answer:**  
Because retail pricing is an evolving time-series forecasting problem, **random splitting causes catastrophic look-ahead leakage** (models learn from future competitor movements and demand to predict past prices).

We enforced a strict **chronological partition**:
- **Training Set (2023-01-15 to 2025-06-30):** 44,668 observations (30.6%)
- **Validation Set (2025-07-01 to 2025-12-31):** 45,590 observations (31.2%)
- **Test Set (2026-01-01 to 2026-08-02):** 55,640 observations (38.1%)

The test partition represents strictly out-of-time future data that the model never touches during development or tuning.

---

### Q6: Why is nominal price $R^2$ so high (~0.99), and is that data leakage?
**Answer:**  
This is a critical interview talking point:
1. **Nominal Scale Dominance:** Product prices range from ₹100 (Grocery items) to ₹9,000+ (Electronics). Because selling price is strongly anchored to `Cost_Price` and `Competitor_Avg_Price`, any linear or non-linear model predicting raw currency naturally achieves a high nominal $R^2$.
2. **Honest Scale-Invariant Evaluation:** To eliminate scale bias, we also evaluated the model on **dynamic markup percentage**:
   $$\text{Markup} = \frac{\text{Optimal Price} - \text{Cost Price}}{\text{Cost Price}}$$
   On this scale-invariant target, LightGBM achieves an **$R^2 = 0.9903$** with an MAE of **₹14.05** (MAPE 1.20%), confirming that the model genuinely masters dynamic contextual multipliers rather than merely memorizing product cost levels.

---

### Q7: Which features are most influential in determining optimal price?
**Answer:**  
Using LightGBM relative gain importance:
1. **`Cost_Price` & `Marketplace_Fee_Pct`:** Anchor unit-level cost economics and profitability baselines.
2. **`Competitor_Avg_Price` & `Price_Gap_Pct`:** Form market pricing elasticity boundaries.
3. **`Price_Elasticity_Score` & `Festival_Impact_Score`:** Drive the dynamic margin multiplier during high-demand cultural surges (Navratri, Diwali).
4. **`Stock_Days_Remaining` & `Return_Rate`:** Apply inventory scarcity surcharges ($<3$ days stock) or clearance markdowns ($>90$ days stock).

---

## 4. Modeling & Machine Learning Strategy

### Q8: What models did you benchmark, and why was LightGBM chosen?
**Answer:**  
We evaluated 5 modeling approaches on the chronological validation set:
1. **Naive Current Price Baseline:** MAE = ₹224.26, Markup $R^2 = 0.0000$ (No dynamic optimization).
2. **Cost-Plus Fixed Markup Baseline:** MAE = ₹171.18, Markup $R^2 = 0.4482$.
3. **Multiple Linear Regression:** MAE = ₹66.75, Markup $R^2 = 0.8115$.
4. **Random Forest Regressor:** MAE = ₹54.20, Markup $R^2 = 0.8850$.
5. **LightGBM Regressor (Tuned):** MAE = ₹14.05, Markup $R^2 = 0.9903$ (Winning model).

**Why LightGBM:**
- Gradient-boosted decision trees naturally capture complex, non-linear interaction effects (e.g., interaction between stock runway, festival proximity, and competitor discounts).
- Histogram-based binning and leaf-wise splitting provide 10x faster inference and lower memory footprint compared to traditional tree ensembles.
- Outperforms deep learning on structured tabular data with 57 features.

---

### Q9: How did you tune LightGBM hyperparameters?
**Answer:**  
We tuned LightGBM on the validation set across tree depth, leaf count, learning rate, and regularizations:
- `n_estimators`: 400
- `learning_rate`: 0.03
- `num_leaves`: 63
- `max_depth`: 9
- `reg_alpha` (L1): 0.05
- `reg_lambda` (L2): 0.10

This configuration prevented overfitting while achieving rapid gradient convergence.

---

### Q10: How does Phase 6 model selection relate to Phase 8 final evaluation?
**Answer:**  
1. **Phase 6:** Evaluated multiple algorithms on the **Validation Set** exclusively to select the winning model *architecture* (LightGBM).
2. **Phase 8:** Retrained the chosen LightGBM architecture **from scratch** on the combined historical dataset (Train + Validation: 90,258 observations) using the best hyperparameters.
3. Evaluated the final retrained model exclusively on the held-out **2026 Test Set** (55,640 observations), ensuring zero data leakage.

---

## 5. Deployment & System Architecture

### Q11: How is the machine learning model served in production?
**Answer:**  
1. **Model Bundle Serialization:** The trained LightGBM model, exact 57 feature column sequence, categorical label encoders, and training metadata are packaged into `models/price_optimizer.pkl`.
2. **FastAPI Microservice (`app.py`):**
   - Loads the serialized bundle once during application startup using an asynchronous `lifespan` context manager.
   - Caches the model in RAM for sub-5ms inference latency.
   - Exposes `POST /predict`, `GET /health`, and `GET /api/catalog-samples`.
   - Mounts the client web application on `/`.
3. **Pydantic Validation:** Strictly validates input types, price positivity, and cost-to-MRP constraints before invoking inference.

---

### Q12: What business guardrails are applied to the raw ML predictions?
**Answer:**  
Machine learning predictions must never be served directly to commercial systems without safeguards. We apply a 3-tier post-inference guardrail layer:
1. **Guaranteed Profit Floor:** Price cannot drop below $\text{Cost Price} \times 1.05$.
2. **Market Competitor Corridor:** Price is clipped within $[0.75 \times \text{Competitor Avg Price}, 1.25 \times \text{Competitor Avg Price}]$.
3. **Catalog Bounds:** Price is bounded within $[\text{Min Allowed Price}, \text{Max Allowed Price}]$.
4. **Action Classifier:** Classifies pricing recommendations into `"Increase Price"`, `"Decrease Price"`, or `"Hold Price"` based on a $\pm 2.0\%$ significance threshold.

---

### Q13: How does the system handle production concept drift?
**Answer:**  
In production, we monitor:
1. **Prediction Drift:** Tracking the distribution of recommended price adjustments vs historical distributions using Kolmogorov-Smirnov (KS) tests.
2. **Input Data Drift:** Tracking macroeconomic fluctuations (USD/INR, inflation) and competitor pricing changes.
3. **Automated Scheduled Retraining:** Retraining model weights monthly on the latest 24 months of rolling transaction data.

---

## 6. Project Trade-offs & Engineering Decisions

### Q14: Why choose vanilla HTML/CSS/JS over React for the frontend?
**Answer:**  
For a dedicated, high-performance operational dashboard with a single input form and real-time result cards:
- Vanilla JavaScript requires **zero build tooling** (no Webpack, Vite, or node_modules overhead).
- Faster initial load times and direct asset serving via FastAPI's static mount.
- Simpler repository architecture that remains accessible and easy to inspect during technical interviews.

---

### Q15: What would you do differently if given 3 months to scale this project?
**Answer:**  
1. **Reinforcement Learning (Contextual Bandits):** Implement a multi-armed bandit (Thompson Sampling or LinUCB) to dynamically explore price elasticity curves live in production without sacrificing revenue.
2. **Cross-Price Elasticity:** Model cannibalization effects between complementary and substitute SKUs within the same category.
3. **Real-Time Streaming Architecture:** Integrate Apache Kafka to stream live clickstream events and competitor scrapers into a feature store (such as Feast).
