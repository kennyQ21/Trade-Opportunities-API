"""
Configuration Module
Loads environment variables and provides centralized settings
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env file"""
    
    # API Keys
    openai_api_key: str
    gnews_api_key: str = ""  # Optional: GNews API for news search (free tier available)
    
    # Rate Limiting
    rate_limit_per_minute: int = 5
    rate_limit_per_hour: int = 30
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Analysis Settings
    default_country: str = "India"
    max_refinement_iterations: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
