"""API v1 package."""
from app.api.v1.predictions import router as predictions_router
from app.api.v1.model_management import router as model_management_router
from app.api.v1.metrics import router as metrics_router

__all__ = ["predictions_router", "model_management_router", "metrics_router"]
