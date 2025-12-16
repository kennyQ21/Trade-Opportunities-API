"""
AI Analyzer Node
Node B in the LangGraph workflow - Generates initial analysis report
"""
import logging
from analysis_engine.graph_state import AnalysisState
from external_tools.ai_client import openai_client

logger = logging.getLogger(__name__)


def analyzer_node(state: AnalysisState) -> AnalysisState:
    """
    Node B: Generates initial market analysis using OpenAI GPT-4o
    
    Args:
        state: Current analysis state with raw_data
        
    Returns:
        Updated state with markdown_report populated
    """
    logger.info(f"[NODE B] Generating: {state['sector']}")
    
    try:
        # Generate analysis using AI client
        report = openai_client.generate_analysis(
            state['sector'],
            state.get('country', 'India'),
            state.get('raw_data', 'No data available')
        )
        
        if report:
            state['markdown_report'] = report
            logger.info(f"[NODE B] Generated {len(report)} chars")
        else:
            state['error'] = "AI analysis returned empty response"
            state['markdown_report'] = _generate_fallback_report(state['sector'], state.get('country', 'India'))
            logger.warning("[NODE B] Using fallback")
            
    except Exception as e:
        logger.error(f"[NODE B] {e}")
        state['error'] = f"AI analysis failed: {str(e)}"
        state['markdown_report'] = _generate_fallback_report(state['sector'], state.get('country', 'India'))
    
    return state


def _generate_fallback_report(sector: str, country: str) -> str:
    """Generate fallback report when AI analysis fails"""
    return f"""# {sector.title()} Sector - Trade Opportunities Analysis ({country})

## Analysis Unavailable

Technical difficulties prevented analysis generation. Please retry or verify OpenAI API configuration.

---
*Sector: {sector.title()} | Market: {country} | Status: Service Issue*
"""
