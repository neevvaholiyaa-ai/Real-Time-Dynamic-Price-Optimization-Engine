"""
Unit Tests for Machine Learning Model Bundle & Prediction Pipeline.
"""
import pytest
from pathlib import Path
import pickle
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
from src.predict import get_model_bundle, predict_optimal_price, validate_input_data

def test_model_bundle_integrity():
    bundle = get_model_bundle()
    assert bundle is not None, "Model bundle failed to load"
    assert "model" in bundle, "Missing 'model' object in bundle"
    assert "feature_columns" in bundle, "Missing 'feature_columns' in bundle"
    assert len(bundle["feature_columns"]) == 57, f"Expected 57 features, got {len(bundle['feature_columns'])}"
    assert "category_mapping" in bundle, "Missing 'category_mapping'"
    assert "city_mapping" in bundle, "Missing 'city_mapping'"
    assert "metrics" in bundle, "Missing 'metrics'"
    assert bundle["metrics"]["test_mae"] < 25.0, "Test MAE exceeds acceptance threshold"

def test_prediction_output_structure():
    sample_payload = {
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
    result = predict_optimal_price(sample_payload)
    assert isinstance(result, dict)
    assert "recommended_price" in result
    assert "price_change" in result
    assert "price_change_percentage" in result
    assert "recommendation" in result
    assert result["recommendation"] in ["Increase Price", "Decrease Price", "Hold Price"]
    assert result["recommended_price"] > 0
    assert result["recommended_price"] >= sample_payload["cost_price"] * 1.05

def test_input_validation_errors():
    # Cost > MRP error
    with pytest.raises(ValueError):
        validate_input_data({
            "cost_price": 5000.0,
            "current_price": 4000.0,
            "mrp": 4500.0,
            "competitor_avg_price": 4200.0
        })

    # Negative price error
    with pytest.raises(ValueError):
        validate_input_data({
            "cost_price": -100.0,
            "current_price": 400.0,
            "mrp": 500.0,
            "competitor_avg_price": 400.0
        })
