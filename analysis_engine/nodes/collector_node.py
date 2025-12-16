"""
Data Collector Node
Node A in the LangGraph workflow - Gathers market intelligence
"""
import logging
from analysis_engine.graph_state import AnalysisState
from external_tools.data_collector import data_collector

logger = logging.getLogger(__name__)


async def collector_node(state: AnalysisState) -> AnalysisState:
    """
    Node A: Collects market data from web sources
    
    This node searches for recent articles and information about the
    specified sector using DuckDuckGo search.
    
    Args:
        state: Current analysis state
        
    Returns:
        Updated state with raw_data and search_results populated
    """
    logger.info(f"[NODE A] Starting: {state['sector']}")
    
    try:
        # Data collector performs I/O operations (HTTP requests with built-in delays)
        data = data_collector.collect_sector_data(state['sector'], state.get('country', 'India'))
        
        # Update state
        state['raw_data'] = data['raw_data']
        state['search_results'] = data['search_results']
        state['data_quality'] = data.get('data_quality', 'unknown')
        state['fallback_used'] = data.get('fallback_used', False)
        
        logger.info(f"[NODE A] Collected {data['total_results']} results")
        
    except Exception as e:
        logger.error(f"[NODE A] {e}")
        state['error'] = f"Data collection failed: {str(e)}"
        state['raw_data'] = "Data collection encountered an error."
        state['search_results'] = []
    
    return state
