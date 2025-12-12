"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.v1 import predictions_router, model_management_router, metrics_router
from loguru import logger
import sys

# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    # Connect to Redis cache
    try:
        from app.cache import cache_manager
        await cache_manager.connect()
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Continuing without cache.")
    
    # Load ML models
    try:
        from app.api.v1.predictions import load_models, warmup_models
        load_models()
        
        # Warm up models with sample data if enabled
        if settings.MODEL_WARMUP:
            logger.info("Warming up models with sample data...")
            await warmup_models()
            logger.info("✅ Models warmed up successfully")
    except Exception as e:
        logger.error(f"Failed to load ML models: {e}")
        if not settings.DEBUG:
            raise
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    # Disconnect from Redis
    try:
        from app.cache import cache_manager
        await cache_manager.disconnect()
    except Exception as e:
        logger.warning(f"Redis disconnect failed: {e}")


# Create FastAPI application
app = FastAPI(
    title="🌊 Guardy AI - Flood Prediction API",
    version=settings.APP_VERSION,
    description="""
## Advanced Flood Prediction & Early Warning System

Production-ready FastAPI microservice providing real-time flood risk assessment, 
nowcasting, anomaly detection, and evacuation zone planning using state-of-the-art 
machine learning models.

### Features

* **🎯 Flood Risk Prediction** - 96.99% accuracy ensemble model
* **📈 Nowcasting** - LSTM-based 1-7 day flood forecasting (93.3% accuracy)
* **🔍 Anomaly Detection** - Isolation Forest for sensor monitoring (98.5% F1-score)
* **🚨 Evacuation Planning** - Real-time evacuation zone generation with GeoJSON
* **📊 Batch Processing** - Process up to 100 locations simultaneously
* **🔄 Hot-Reload** - Update ML models without server downtime

### ML Models

1. **FloodRiskScorer** - Random Forest + Gradient Boosting Ensemble
2. **FloodNowcaster** - LSTM Neural Network (2-layer, 64/32 units)
3. **SensorAnomalyDetector** - Isolation Forest

### Quick Links

* [GitHub Repository](https://github.com/HenryTech12/Guardy)
* [API Examples](https://github.com/HenryTech12/Guardy/blob/master/ai-microservice/docs/API_EXAMPLES.md)
* [Testing Guide](https://github.com/HenryTech12/Guardy/blob/master/ai-microservice/tests/README.md)
    """,
    summary="AI-powered flood prediction and early warning system",
    version=settings.APP_VERSION,
    terms_of_service="https://github.com/HenryTech12/Guardy/blob/master/TERMS.md",
    contact={
        "name": "Guardy Support Team",
        "url": "https://github.com/HenryTech12/Guardy",
        "email": "support@guardy.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "predictions",
            "description": "ML prediction endpoints for flood risk assessment, nowcasting, and anomaly detection",
        },
        {
            "name": "model-management",
            "description": "Model management operations including status, metadata, reload, and statistics",
        },
        {
            "name": "health",
            "description": "Health check and system status endpoints",
        },
    ],
    lifespan=lifespan,
)

# Configure CORS
# NOTE: For production deployment, replace allow_origins=["*"] with specific frontend URLs
# Example: allow_origins=["https://floodguard.com", "https://www.floodguard.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(predictions_router)
app.include_router(model_management_router)
app.include_router(metrics_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
