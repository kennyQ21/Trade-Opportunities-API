"""
Formatter Node (Node E)
Extracts structured data from the final validated markdown report
"""
import logging
from analysis_engine.graph_state import AnalysisState
from external_tools.ai_client import openai_client

logger = logging.getLogger(__name__)


def formatter_node(state: AnalysisState) -> AnalysisState:
    """
    Node E: Extracts structured data from validated markdown report
    
    Uses GPT-4o-mini to extract key metrics into JSON format.
    
    Args:
        state: Current analysis state with validated markdown_report
        
    Returns:
        Updated state with json_summary field populated
    """
    logger.info(f"[NODE E] Extracting: {state['sector']}")
    
    try:
        # Extract structured data using AI
        json_summary = openai_client.format_report(state.get('markdown_report', ''), state['sector'])
        
        state['json_summary'] = json_summary
        logger.info(f"[NODE E] Extracted {len(json_summary.get('top_recommendations', []))} items")
        
        return state
        
    except Exception as e:
        logger.error(f"[NODE E] {e}")
        
        # Fallback: Set minimal structure
        state['json_summary'] = {
            'market_size': None,
            'growth_cagr': None,
            'top_recommendations': []
        }
        return state
