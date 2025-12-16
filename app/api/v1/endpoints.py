"""
API Endpoints Module
Defines all FastAPI routes for the Trade Opportunities API
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import PlainTextResponse
from datetime import datetime
import logging
import uuid

from app.models import StructuredAnalysisResponse, DataSummary, User, Source
from app.core.auth import get_current_user
from app.services.in_memory_store import rate_limiter
from analysis_engine.analysis_graph import execute_analysis

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


@router.get("/", tags=["Root"])
async def root():
    """API root endpoint with service information"""
    return {
        "service": "Trade Opportunities API",
        "version": "1.0.0",
        "architecture": "FastAPI + LangGraph + OpenAI",
        "documentation": "/docs",
        "endpoints": {
            "analysis": "/v1/analyze/{sector}",
            "download": "/v1/analyze/{sector}/download",
            "rate_limits": "/v1/rate-limits",
            "health": "/health"
        }
    }


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Trade Opportunities API",
        "version": "1.0.0"
    }


@router.get(
    "/v1/analyze/{sector}",
    response_model=StructuredAnalysisResponse,
    tags=["Analysis"],
    responses={
        400: {"description": "Invalid sector parameter"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def analyze_sector(
    sector: str,
    current_user: User = Depends(get_current_user)
) -> StructuredAnalysisResponse:
    """
    Analyze a specific sector using LangGraph multi-agent workflow
    
    **LangGraph Workflow:**
    1. **Data Collector Node**: Gathers market data from web sources
    2. **AI Analyzer Node**: Generates initial comprehensive report
    3. **Report Critic Node**: Reviews quality and completeness
    4. **Report Refiner Node**: Improves report based on feedback (if needed)
    5. **Self-Correction Loop**: Repeats critic → refiner up to 2 times
    
    **Parameters:**
    - **sector**: Name of the sector (e.g., pharmaceuticals, technology, agriculture)
    
    **Authentication:**
    - Optional: Use X-API-Key header for authenticated access
    - Guest access available without authentication (lower priority)
    - Demo API keys: demo-key-12345, guest-key-67890
    
    **Rate Limits:**
    - 5 requests per minute
    - 30 requests per hour (per user/API key)
    
    **Returns:**
    - High-quality, self-corrected markdown report with market analysis
    """
    
    sector = sector.strip().lower()
    user_id = current_user.username
    
    # Check rate limits
    allowed, message = await rate_limiter.check_rate_limit(user_id)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)
    
    logger.info(f"🚀 [API] Starting LangGraph workflow for: {sector} (user: {user_id})")
    
    try:
        # Execute LangGraph workflow (async)
        final_state = await execute_analysis(sector, "India")
        
        # Extract results
        analysis_report = final_state.get('markdown_report', '')
        iterations = final_state.get('iterations', 0)
        error = final_state.get('error')
        
        # Log completion
        remaining = rate_limiter.get_remaining_requests(user_id)
        if error:
            logger.warning(f"⚠️ [API] {sector} completed with issues (iter: {iterations}). {error}")
        else:
            logger.info(f"✅ [API] {sector} completed (iter: {iterations}). Remaining: {remaining['per_minute']}/min")
        
        # Extract structured data summary
        json_summary = final_state.get('json_summary', {})
        data_summary = DataSummary(
            market_size=json_summary.get('market_size'),
            growth_cagr=json_summary.get('growth_cagr'),
            top_recommendations=json_summary.get('top_recommendations', [])
        )
        
        # Extract sources from search results (limited to top 10)
        sources = [
            Source(
                title=result.get('title', ''),
                url=result.get('url', ''),
                source=result.get('source', ''),
                snippet=result.get('snippet', '')
            )
            for result in final_state.get('search_results', [])[:10]
        ]
        
        # Return structured JSON with embedded markdown
        return StructuredAnalysisResponse(
            status="success",
            report_id=str(uuid.uuid4()),
            sector=sector,
            timestamp=final_state.get('timestamp', datetime.utcnow().isoformat()),
            data_summary=data_summary,
            markdown_body=analysis_report,
            sources=sources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [API] Error during workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analysis: {str(e)}"
        )


@router.get(
    "/v1/analyze/{sector}/download",
    response_class=PlainTextResponse,
    tags=["Analysis"]
)
async def download_analysis(
    sector: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download sector analysis as a markdown file
    
    Note: This runs a full analysis. For production, consider caching results
    or requiring clients to POST the report they want to download.
    """
    analysis_response = await analyze_sector(sector, current_user)
    
    return PlainTextResponse(
        content=analysis_response.markdown_body,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={sector}_analysis_{datetime.utcnow().strftime('%Y%m%d')}.md"}
    )


@router.get("/v1/rate-limits", tags=["Monitoring"])
async def get_rate_limits(current_user: User = Depends(get_current_user)):
    """
    Get current rate limit status for the authenticated user
    
    Returns information about:
    - Total limits configured
    - Remaining requests in current time windows
    - User identification
    """
    from app.core.config import settings
    
    user_id = current_user.username
    remaining = rate_limiter.get_remaining_requests(user_id)
    
    return {
        "user": user_id,
        "limits": {
            "per_minute": settings.rate_limit_per_minute,
            "per_hour": settings.rate_limit_per_hour
        },
        "remaining": remaining,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/v1/api-keys", tags=["API Keys"])
async def generate_api_key(user_id: str):
    """
    Generate a new API key for a user
    
    Note: In production, this should require admin authentication
    
    Args:
        user_id: Identifier for the user
    
    Returns:
        API key information
    """
    from app.services.in_memory_store import api_key_store
    
    api_key = api_key_store.generate_key(user_id)
    
    return {
        "user_id": user_id,
        "api_key": api_key,
        "message": "Store this key securely. It cannot be retrieved later.",
        "usage": "Include in X-API-Key header for authenticated requests"
    }
