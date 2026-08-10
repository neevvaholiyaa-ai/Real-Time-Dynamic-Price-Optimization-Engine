"""
Pydantic schemas for request validation and response serialization.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class PricePredictionRequest(BaseModel):
    product_id: Optional[str] = Field(default="PROD-ELEC-001", description="Unique SKU / Product Identifier")
    product_name: Optional[str] = Field(default="Wireless Noise Cancelling Headphones Pro", description="Product Name")
    category: str = Field(default="Electronics", description="Retail category")
    city: str = Field(default="Ahmedabad", description="Fulfillment Hub City (Ahmedabad or Surat)")
    cost_price: float = Field(..., gt=0, description="Unit acquisition / cost price in INR")
    current_price: float = Field(..., gt=0, description="Current active selling price in INR")
    mrp: float = Field(..., gt=0, description="Maximum retail price in INR")
    competitor_avg_price: float = Field(..., gt=0, description="Competitor average selling price in INR")
    stock_level: int = Field(default=100, ge=0, description="Current stock units in warehouse")
    orders: int = Field(default=45, ge=0, description="Daily sales velocity / orders")
    days_until_next_festival: int = Field(default=30, ge=0, description="Days remaining until next regional festival")
    weather_type: str = Field(default="Clear", description="Current weather (Clear, Rainy, Overcast, Partly Cloudy)")
    competitor_stock_status: str = Field(default="In_Stock", description="Competitor stock status (In_Stock, Low_Stock, Out_of_Stock)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "P001",
                "product_name": "Wireless Noise Cancelling Headphones Pro",
                "category": "Electronics",
                "city": "Ahmedabad",
                "cost_price": 2500.0,
                "current_price": 4200.0,
                "mrp": 4999.0,
                "competitor_avg_price": 4150.0,
                "stock_level": 25,
                "orders": 65,
                "days_until_next_festival": 3,
                "weather_type": "Clear",
                "competitor_stock_status": "In_Stock"
            }
        }
    }

class PricePredictionResponse(BaseModel):
    product_id: Optional[str] = "P001"
    city: Optional[str] = "Ahmedabad"
    current_price: float
    recommended_price: float
    price_change: float
    price_change_percent: float
    recommendation: str
    guardrail_applied: bool = False
    min_allowed_price: float = 0.0
    max_allowed_price: float = 0.0
    insights: List[str] = []
