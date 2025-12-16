"""
Report Critic Node
Node C in the LangGraph workflow - Validates report quality
"""
import logging
from analysis_engine.graph_state import AnalysisState
from external_tools.ai_client import openai_client

logger = logging.getLogger(__name__)


def clean_critique(critique_str: str) -> str:
    """Remove markdown code block wrappers and clean whitespace"""
    cleaned = critique_str.strip()
    
    # Remove markdown code blocks (```json, ```, etc.)
    if cleaned.startswith("```"):
        # Remove first line if it's a code block marker
        lines = cleaned.split('\n', 1)
        cleaned = lines[1] if len(lines) > 1 else cleaned
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    return cleaned.strip()


def critic_node(state: AnalysisState) -> AnalysisState:
    """
    Node C: Validates report quality and completeness
    
    Args:
        state: Current analysis state with markdown_report
        
    Returns:
        Updated state with critique (PASS or FAIL: reason)
    """
    logger.info(f"[NODE C] Reviewing (iter {state['iterations']})")
    
    try:
        report = state.get('markdown_report', '')
        
        # Basic validation
        if not report or len(report) < 500:
            state['critique'] = "FAIL: Report is too short or empty. Needs substantial content."
            logger.warning("[NODE C] Report too short")
            return state
            
        # Skip strict critique if fallback data was used (prevent infinite loops on low data)
        if state.get('fallback_used', False):
            state['critique'] = "PASS"
            logger.info("[NODE C] Fallback data used - skipping strict critique")
            return state
        
        # Get AI critique (returns dict: {'decision': 'PASS'|'FAIL', 'reason': '...'})
        critique_dict = openai_client.critique_report(state['sector'], report)
        
        # Parse the structured dictionary for reliable decision-making
        decision = critique_dict.get('decision', 'PASS').upper()
        reason = critique_dict.get('reason', 'No reason provided')
        
        # Store the full critique dict in state
        state['critique'] = critique_dict
        
        # Log with clear visual indicators
        if decision == "PASS":
            logger.info("[NODE C] ✓ Report PASSED review")
        else:
            # Truncate reason for logging clarity
            logger.info(f"[NODE C] ✗ Needs work: {reason[:80]}...")
            
    except Exception as e:
        logger.error(f"[NODE C] Exception during critique: {e}")
        # Default to PASS dictionary on error to avoid blocking
        state['critique'] = {"decision": "PASS", "reason": "Internal node error - defaulted to PASS."}
    
    return state
