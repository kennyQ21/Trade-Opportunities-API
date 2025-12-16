"""
Trade Opportunities API - Main Entry Point
FastAPI application with LangGraph multi-agent workflow
"""
from fastapi import FastAPI
import logging

from app.api.v1.endpoints import router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Trade Opportunities API",
    description="""
    AI-powered market analysis and trade opportunity insights for Indian sectors.
    
    ## Architecture
    
    This API uses **LangGraph** to implement a sophisticated multi-agent workflow:
    
    1. **Data Collector Node**: Gathers real-time market intelligence
    2. **AI Analyzer Node**: Generates comprehensive analysis with OpenAI GPT-4o
    3. **Report Critic Node**: Validates quality and completeness
    4. **Report Refiner Node**: Improves based on feedback
    5. **Formatter Node**: Extracts structured data
    6. **Self-Correction Loop**: Ensures high-quality output
    
    ## Features
    
    - 🔄 5-node LangGraph workflow with self-correction
    - 🤖 OpenAI GPT-4o integration
    - 🔒 API key authentication with guest access
    - ⚡ Rate limiting (5/min, 30/hr per user)
    - 🔍 Real-time data collection (GNews API)
    - 📊 Quality-validated structured reports
    
    ## Authentication
    
    - **Authenticated**: Include `X-API-Key` header (demo keys: demo-key-12345, guest-key-67890)
    - **Guest Access**: No authentication required (limited priority)
    
    ## Rate Limits
    
    - 5 requests per minute
    - 30 requests per hour
    - Per user/API key tracking
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Trade Opportunities API",
        "url": "https://github.com/yourusername/trade-opportunities-api"
    },
    license_info={
        "name": "MIT"
    }
)

# Include API router
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    logger.info("=" * 60)
    logger.info("🚀 Trade Opportunities API Starting")
    logger.info("=" * 60)
    logger.info(f"📍 Server: http://{settings.host}:{settings.port}")
    logger.info(f"📚 Docs: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🔒 Rate Limits: {settings.rate_limit_per_minute}/min, {settings.rate_limit_per_hour}/hr")
    logger.info(f"🔄 Max Refinement Iterations: {settings.max_refinement_iterations}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information"""
    logger.info("👋 Trade Opportunities API Shutting Down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
