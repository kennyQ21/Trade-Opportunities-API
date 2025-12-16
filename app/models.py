from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    """User model for authentication"""
    username: str
    disabled: Optional[bool] = None


class Source(BaseModel):
    """Source citation with metadata"""
    title: str
    url: str
    source: str
    snippet: Optional[str] = None


class DataSummary(BaseModel):
    """Extracted key metrics from analysis report"""
    market_size: Optional[str] = None
    growth_cagr: Optional[str] = None
    top_recommendations: list[str] = []


class StructuredAnalysisResponse(BaseModel):
    """Structured API response with JSON summary and full markdown report"""
    status: str = "success"
    report_id: str
    sector: str
    timestamp: str
    data_summary: DataSummary
    markdown_body: str
    sources: list[Source] = []
