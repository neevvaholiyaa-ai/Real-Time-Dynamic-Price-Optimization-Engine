"""
Pydantic schemas for request validation, data transfer, and response serialization.
Strictly types user input, model predictions, database entities, and analytics.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# 1. AUTH SCHEMAS
# -----------------------------------------------------------------------------
class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, description="User email address")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    display_name: Optional[str] = Field(default=None, description="User or Store display name")

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    created_at: Optional[str] = None

# -----------------------------------------------------------------------------
# 2. PRODUCT SCHEMAS
# -----------------------------------------------------------------------------
class ProductCreateRequest(BaseModel):
    product_name: str = Field(..., min_length=1, description="Product Name")
    category: Optional[str] = Field(default="Electronics", description="Retail category")
    brand: Optional[str] = None
    sku: Optional[str] = None
    location: Optional[str] = None

    cost_price: float = Field(..., gt=0, description="Unit acquisition cost price")
    current_price: float = Field(..., gt=0, description="Current selling price")
    mrp: float = Field(..., gt=0, description="Maximum retail price")
    minimum_price: Optional[float] = Field(default=None, gt=0, description="Custom floor price")
    maximum_price: Optional[float] = Field(default=None, gt=0, description="Custom ceiling price")
    target_margin: Optional[float] = Field(default=None, ge=0, description="Target gross margin percentage")

    stock_quantity: Optional[int] = Field(default=None, ge=0, description="Warehouse stock level")
    average_daily_sales: Optional[float] = Field(default=None, ge=0, description="Average daily unit sales")
    reorder_threshold: Optional[int] = Field(default=None, ge=0, description="Inventory reorder point")

    competitor_price: Optional[float] = Field(default=None, gt=0, description="Competitor average selling price")
    competitor_name: Optional[str] = Field(default=None, description="Competitor / marketplace name")
    business_goal: Optional[str] = Field(default="balanced", description="Business objective")

class ProductUpdateRequest(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    location: Optional[str] = None

    cost_price: Optional[float] = Field(default=None, gt=0)
    current_price: Optional[float] = Field(default=None, gt=0)
    mrp: Optional[float] = Field(default=None, gt=0)
    minimum_price: Optional[float] = None
    maximum_price: Optional[float] = None
    target_margin: Optional[float] = None

    stock_quantity: Optional[int] = None
    average_daily_sales: Optional[float] = None
    reorder_threshold: Optional[int] = None

    competitor_price: Optional[float] = None
    competitor_name: Optional[str] = None
    business_goal: Optional[str] = None

class ProductResponse(BaseModel):
    product_id: str
    user_id: str
    product_name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    sku: Optional[str] = None
    location: Optional[str] = None

    cost_price: float
    current_price: float
    mrp: float
    minimum_price: Optional[float] = None
    maximum_price: Optional[float] = None
    target_margin: Optional[float] = None

    stock_quantity: Optional[int] = None
    average_daily_sales: Optional[float] = None
    reorder_threshold: Optional[int] = None

    competitor_price: Optional[float] = None
    competitor_name: Optional[str] = None
    business_goal: Optional[str] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

# -----------------------------------------------------------------------------
# 3. ANALYSIS SCHEMAS
# -----------------------------------------------------------------------------
class AnalysisResponse(BaseModel):
    analysis_id: str
    user_id: str
    product_id: str
    product_name: Optional[str] = None
    category: Optional[str] = None

    input_cost_price: float
    input_current_price: float
    input_mrp: float
    input_competitor_price: Optional[float] = None
    input_stock_quantity: Optional[int] = None
    input_daily_orders: Optional[float] = None

    recommended_price: float
    price_change: float
    price_change_pct: float
    recommendation: str

    margin_current_pct: float
    margin_recommended_pct: float
    margin_lift_pct: float
    competitor_gap_pct: Optional[float] = None
    stock_runway_days: Optional[float] = None
    expected_demand: Optional[float] = None
    expected_revenue_30d: Optional[float] = None
    expected_profit_30d: Optional[float] = None

    confidence_level: str  # 'high' | 'medium' | 'low'
    confidence_details: List[str] = []

    guardrail_applied: bool = False
    guardrail_details: List[Dict[str, Any]] = []
    min_allowed_price: float
    max_allowed_price: float

    insights: List[str] = []
    economic_drivers: List[Dict[str, Any]] = []
    feature_provenance: Dict[str, str] = {}

    status: str = "pending"
    applied_at: Optional[str] = None
    created_at: Optional[str] = None

# -----------------------------------------------------------------------------
# 4. SALES HISTORY SCHEMAS
# -----------------------------------------------------------------------------
class SalesRecordCreateRequest(BaseModel):
    period_date: str = Field(..., description="Date or period string e.g. YYYY-MM-DD or YYYY-MM")
    units_sold: int = Field(..., ge=0)
    selling_price: float = Field(..., gt=0)
    revenue: Optional[float] = None
    cost: Optional[float] = None
    profit: Optional[float] = None
    source: Optional[str] = "user_input"

class SalesRecordResponse(BaseModel):
    record_id: str
    user_id: str
    product_id: str
    period_date: str
    units_sold: int
    selling_price: float
    revenue: float
    cost: float
    profit: float
    source: str
    created_at: Optional[str] = None

# -----------------------------------------------------------------------------
# 5. PRICING HISTORY SCHEMAS
# -----------------------------------------------------------------------------
class PricingHistoryResponse(BaseModel):
    history_id: str
    user_id: str
    product_id: str
    analysis_id: Optional[str] = None
    old_price: float
    new_price: float
    change_pct: float
    reason: Optional[str] = None
    created_at: Optional[str] = None

# -----------------------------------------------------------------------------
# 6. USER SETTINGS SCHEMAS
# -----------------------------------------------------------------------------
class UserSettingsRequest(BaseModel):
    margin_floor_pct: float = Field(default=5.5, ge=0, le=50)
    corridor_min_pct: float = Field(default=-25.0, ge=-50, le=0)
    corridor_max_pct: float = Field(default=25.0, ge=0, le=50)
    max_discount_pct: float = Field(default=40.0, ge=0, le=90)
    max_price_change_pct: float = Field(default=15.0, ge=1, le=50)
    never_below_cost: bool = True
    never_above_mrp: bool = True
    custom_price_floor: Optional[float] = None
    custom_price_ceiling: Optional[float] = None
    currency: str = "INR"
    store_name: Optional[str] = None

class UserSettingsResponse(BaseModel):
    user_id: str
    margin_floor_pct: float
    corridor_min_pct: float
    corridor_max_pct: float
    max_discount_pct: float
    max_price_change_pct: float
    never_below_cost: bool
    never_above_mrp: bool
    custom_price_floor: Optional[float] = None
    custom_price_ceiling: Optional[float] = None
    currency: str
    store_name: Optional[str] = None

# -----------------------------------------------------------------------------
# 7. DASHBOARD SCHEMAS
# -----------------------------------------------------------------------------
class DashboardOverviewResponse(BaseModel):
    products_analyzed_count: int
    avg_margin_lift_pct: Optional[float] = None
    price_elasticity_index: Optional[float] = None
    competitor_gap_avg_pct: Optional[float] = None
    competitor_status_label: str = "No competitor data provided"
    stock_runway_avg_days: Optional[float] = None
    stock_status_label: str = "No inventory data provided"
    pending_actions_count: int
    projected_profit_opportunity_30d: Optional[float] = None
    projected_revenue_opportunity_30d: Optional[float] = None
    signals: List[Dict[str, Any]] = []

class DashboardQueueItem(BaseModel):
    analysis_id: str
    product_id: str
    product_name: str
    category: str
    cost_price: float
    current_price: float
    recommended_price: float
    price_change: float
    price_change_pct: float
    competitor_price: Optional[float] = None
    competitor_gap_pct: Optional[float] = None
    stock_runway_days: Optional[float] = None
    confidence_level: str
    margin_lift_pct: float
    projected_profit_lift_30d: Optional[float] = None
    status: str
    created_at: Optional[str] = None

class DashboardAnalyticsResponse(BaseModel):
    total_products_count: int
    total_analyzed_count: int
    has_actual_sales_data: bool
    actual_historical_revenue: Optional[float] = None
    actual_historical_profit: Optional[float] = None
    projected_total_revenue_30d: Optional[float] = None
    projected_total_profit_30d: Optional[float] = None
    projected_incremental_profit_lift_30d: Optional[float] = None
    category_margin_breakdown: List[Dict[str, Any]] = []
    sales_trajectory: List[Dict[str, Any]] = []

# -----------------------------------------------------------------------------
# 8. SIMULATION / PREDICTION SCHEMAS (Stateless)
# -----------------------------------------------------------------------------
class PricePredictionRequest(BaseModel):
    product_id: Optional[str] = Field(default="PROD-SIM-001")
    product_name: Optional[str] = Field(default="Target SKU")
    category: str = Field(default="Electronics")
    city: Optional[str] = Field(default="Ahmedabad")
    cost_price: float = Field(..., gt=0)
    current_price: float = Field(..., gt=0)
    mrp: float = Field(..., gt=0)
    competitor_avg_price: Optional[float] = Field(default=None, gt=0)
    stock_level: Optional[int] = Field(default=None, ge=0)
    orders: Optional[int] = Field(default=None, ge=0)
    days_until_next_festival: Optional[int] = Field(default=None, ge=0)
    weather_type: Optional[str] = Field(default=None)
    competitor_stock_status: Optional[str] = Field(default=None)
    business_goal: Optional[str] = Field(default="balanced")

class PricePredictionResponse(BaseModel):
    product_id: Optional[str] = "PROD-SIM-001"
    product_name: Optional[str] = "Target SKU"
    category: Optional[str] = "Electronics"
    city: Optional[str] = None
    current_price: float
    recommended_price: float
    price_change: float
    price_change_percent: float
    recommendation: str
    guardrail_applied: bool = False
    guardrail_details: List[Dict[str, Any]] = []
    min_allowed_price: float = 0.0
    max_allowed_price: float = 0.0
    confidence_level: str = "medium"
    confidence_details: List[str] = []
    insights: List[str] = []
    economic_drivers: List[Dict[str, Any]] = []
    feature_provenance: Dict[str, str] = {}
    topology_curve: List[Dict[str, Any]] = []
