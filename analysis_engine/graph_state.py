"""
Graph State Module
Defines the state schema for the LangGraph workflow
"""
from typing import TypedDict, Optional, List, Dict


class AnalysisState(TypedDict):
    """
    State object that flows through the LangGraph workflow
    
    This state is passed between nodes and tracks the entire analysis process.
    Each node reads from and writes to this state.
    
    Attributes:
        sector: The sector to analyze (e.g., "pharmaceuticals")
        country: Target country for analysis (default: "India")
        raw_data: Collected market data from web sources
        search_results: List of search results with metadata
        markdown_report: The generated markdown analysis report
        critique: Feedback from the critic node (PASS or FAIL: reason)
        iterations: Number of refinement cycles completed
        error: Any error message that occurred during processing
        timestamp: ISO timestamp when analysis started
        json_summary: Structured JSON summary extracted from final report
    """
    sector: str
    country: str
    raw_data: Optional[str]
    search_results: Optional[List[Dict[str, str]]]
    markdown_report: Optional[str]
    critique: Optional[str]
    iterations: int
    error: Optional[str]
    timestamp: str
    json_summary: Optional[Dict[str, any]]
    data_quality: Optional[str]
    fallback_used: Optional[bool]
