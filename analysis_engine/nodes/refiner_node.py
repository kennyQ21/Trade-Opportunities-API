"""
Report Refiner Node
Node D in the LangGraph workflow - Improves report based on feedback
"""
import logging
from analysis_engine.graph_state import AnalysisState
from external_tools.ai_client import openai_client

logger = logging.getLogger(__name__)


def refiner_node(state: AnalysisState) -> AnalysisState:
    """
    Node D: Refines report based on critic feedback
    
    Args:
        state: Current analysis state with markdown_report and critique
        
    Returns:
        Updated state with refined markdown_report and incremented iterations
    """
    logger.info("[NODE D] Refining")
    
    try:
        # Extract critique reason from dict or use raw string
        critique = state.get('critique', {})
        critique_text = critique.get('reason', str(critique)) if isinstance(critique, dict) else str(critique)
        
        # Generate refined version using AI client
        refined_report = openai_client.refine_report(
            state['sector'],
            state.get('country', 'India'),
            state.get('markdown_report', ''),
            critique_text,
            state.get('raw_data', '')
        )
        
        if refined_report:
            state['markdown_report'] = refined_report
            logger.info("[NODE D] Refined")
        else:
            logger.warning("[NODE D] Failed, keeping original")
            
    except Exception as e:
        logger.error(f"[NODE D] {e}")
    finally:
        # Always increment iteration counter exactly once
        state['iterations'] = state.get('iterations', 0) + 1
    
    return state
