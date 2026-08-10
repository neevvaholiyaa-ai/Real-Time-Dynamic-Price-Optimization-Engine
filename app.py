"""
FastAPI Backend for Real-Time Dynamic Price Optimization Engine.
Serves prediction endpoints and mounts the frontend dynamic pricing dashboard.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.predict import predict_optimal_price, get_model_bundle

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load model bundle into memory at server startup."""
    try:
        bundle = get_model_bundle()
        print(f"[FastAPI Startup] Model loaded successfully ({len(bundle['feature_columns'])} features).")
    except Exception as e:
        print(f"[FastAPI Startup Error] Could not load model: {e}")
    yield

# Initialize FastAPI App
app = FastAPI(
    title="Real-Time Dynamic Price Optimization Engine",
    description="Dynamic pricing intelligence and profit maximization microservice for e-commerce.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Pydantic Schemas
# =============================================================================

class PricePredictionRequest(BaseModel):
    product_id: Optional[str] = Field(default="PROD-ELEC-001", description="Unique Product SKU ID")
    product_name: Optional[str] = Field(default="Wireless Noise Cancelling Headphones", description="Commercial product name")
    category: str = Field(default="Electronics", description="Retail category (e.g., Electronics, Fashion, Grocery)")
    city: str = Field(default="Ahmedabad", description="Fulfillment hub city (Ahmedabad or Surat)")
    cost_price: float = Field(..., gt=0, description="Unit acquisition / manufacturing cost in INR")
    current_price: float = Field(..., gt=0, description="Current selling price in INR")
    mrp: float = Field(..., gt=0, description="Maximum Retail Price (MRP) printed on packaging in INR")
    competitor_avg_price: float = Field(..., gt=0, description="Competitor average selling price in INR")
    stock_level: int = Field(default=120, ge=0, description="Available warehouse stock units")
    orders: int = Field(default=45, ge=0, description="Recent daily orders / sales velocity")
    days_until_next_festival: int = Field(default=30, ge=0, description="Days remaining until next regional festival")
    weather_type: str = Field(default="Clear", description="Current weather type (Clear, Rainy, Overcast, Partly Cloudy)")
    competitor_stock_status: str = Field(default="In_Stock", description="Competitor stock status (In_Stock, Low_Stock, Out_of_Stock)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "PROD-ELEC-001",
                "product_name": "Wireless Noise Cancelling Headphones Pro",
                "category": "Electronics",
                "city": "Ahmedabad",
                "cost_price": 2500.0,
                "current_price": 4200.0,
                "mrp": 4999.0,
                "competitor_avg_price": 4150.0,
                "stock_level": 45,
                "orders": 60,
                "days_until_next_festival": 3,
                "weather_type": "Clear",
                "competitor_stock_status": "In_Stock"
            }
        }
    }

class PricePredictionResponse(BaseModel):
    current_price: float
    recommended_price: float
    price_change: float
    price_change_percentage: float
    recommendation: str
    guardrail_applied: bool
    min_allowed_price: float
    max_allowed_price: float
    insights: List[str]

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", tags=["System"])
def health_check():
    """
    Health check endpoint returning system status and model readiness.
    """
    try:
        bundle = get_model_bundle()
        model_ready = bundle is not None and "model" in bundle
    except Exception:
        model_ready = False

    return {
        "status": "healthy" if model_ready else "degraded",
        "service": "Dynamic Price Optimization Engine",
        "model_loaded": model_ready
    }

@app.post("/predict", response_model=PricePredictionResponse, tags=["Pricing"])
def predict_price(payload: PricePredictionRequest):
    """
    Computes profit-maximizing recommended price subject to real-time market context
    and strict operational retail guardrails.
    """
    try:
        input_dict = payload.model_dump()
        result = predict_optimal_price(input_dict)
        return PricePredictionResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Prediction error: {str(e)}")

@app.get("/api/catalog-samples", tags=["Catalog"])
def get_catalog_samples():
    """
    Provides curated product presets representing diverse e-commerce retail scenarios.
    """
    return [
        {
            "label": "Wireless Headphones (Electronics, Low Stock, Festive Peak)",
            "product_id": "PROD-ELEC-001",
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
        },
        {
            "label": "Basmati Rice 5kg (Grocery, High Stock, Monsoon)",
            "product_id": "PROD-GROC-001",
            "product_name": "Royal Premium Basmati Rice 5kg",
            "category": "Grocery",
            "city": "Surat",
            "cost_price": 420.0,
            "current_price": 640.0,
            "mrp": 750.0,
            "competitor_avg_price": 650.0,
            "stock_level": 450,
            "orders": 35,
            "days_until_next_festival": 60,
            "weather_type": "Rainy",
            "competitor_stock_status": "In_Stock"
        },
        {
            "label": "Designer Cotton Kurta (Fashion, Festival Approaching)",
            "product_id": "PROD-FASH-003",
            "product_name": "Handcrafted Bandhani Festive Kurta",
            "category": "Fashion",
            "city": "Ahmedabad",
            "cost_price": 650.0,
            "current_price": 1299.0,
            "mrp": 1999.0,
            "competitor_avg_price": 1350.0,
            "stock_level": 90,
            "orders": 48,
            "days_until_next_festival": 5,
            "weather_type": "Clear",
            "competitor_stock_status": "Low_Stock"
        },
        {
            "label": "Smart Fitness Watch (Electronics, Overstock Clearance)",
            "product_id": "PROD-ELEC-004",
            "product_name": "Smart Fitness Watch 1.83 inch",
            "category": "Electronics",
            "city": "Surat",
            "cost_price": 1400.0,
            "current_price": 2899.0,
            "mrp": 3499.0,
            "competitor_avg_price": 2750.0,
            "stock_level": 600,
            "orders": 12,
            "days_until_next_festival": 45,
            "weather_type": "Clear",
            "competitor_stock_status": "In_Stock"
        }
    ]

# =============================================================================
# Mount Static Files & Root Route
# =============================================================================

FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/", tags=["Frontend"])
def serve_dashboard():
    """Serves the main pricing dashboard web application."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({
        "message": "Dynamic Pricing API is running. Frontend index.html is being initialized."
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
