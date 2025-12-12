"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)
    
    # Application
    APP_NAME: str = "FloodGuard AI Microservice"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    RELOAD: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://floodguard_user:your_password@localhost:5432/floodguard"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "floodguard"
    DB_USER: str = "floodguard_user"
    DB_PASSWORD: str = "your_password"
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_ENABLED: bool = True
    
    # Cache TTL (seconds)
    CACHE_TTL_FLOOD_RISK: int = 300  # 5 minutes
    CACHE_TTL_NOWCAST: int = 600  # 10 minutes
    CACHE_TTL_ANOMALY: int = 60  # 1 minute
    CACHE_TTL_BATCH: int = 180  # 3 minutes
    CACHE_TTL_EVACUATION: int = 900  # 15 minutes
    
    # Performance
    MAX_BATCH_SIZE: int = 100
    WORKER_THREADS: int = 4
    PREDICTION_TIMEOUT: int = 30  # seconds
    ENABLE_PROFILING: bool = False
    
    # External APIs
    OPENWEATHER_API_KEY: Optional[str] = None
    
    # Models
    MODEL_PATH: str = "./models"
    ENABLE_MODEL_CACHING: bool = True
    MODEL_WARMUP: bool = True  # Pre-load models with sample data


# Global settings instance
settings = Settings()
