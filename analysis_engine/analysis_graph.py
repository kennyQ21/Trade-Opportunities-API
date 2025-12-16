"""
Analysis Graph Module
Constructs and compiles the LangGraph workflow for sector analysis
"""
from langgraph.graph import StateGraph, END
from datetime import datetime
import logging

from analysis_engine.graph_state import AnalysisState
from analysis_engine.nodes.collector_node import collector_node
from analysis_engine.nodes.analyzer_node import analyzer_node
from analysis_engine.nodes.critic_node import critic_node
from analysis_engine.nodes.refiner_node import refiner_node
from analysis_engine.nodes.formatter_node import formatter_node
from app.core.config import settings

logger = logging.getLogger(__name__)


def should_continue_refinement(state: AnalysisState) -> str:
    """
    Conditional edge: Determines if report needs refinement or is complete
    
    Logic:
    - If critique is PASS OR iterations >= max: Go to FORMATTER
    - If critique is FAIL AND iterations < max: Go to REFINER
    
    This prevents infinite loops while allowing quality improvements.
    
    Args:
        state: Current analysis state
        
    Returns:
        "format" to go to formatter or "refine" to continue refinement
    """
    critique = state.get('critique', {'decision': 'PASS'})
    iterations = state.get('iterations', 0)
    max_iterations = settings.max_refinement_iterations
    
    # Safety: Max iteration limit
    if iterations >= max_iterations:
        logger.info(f"[DECISION] Max iterations reached ({iterations}), proceeding to FORMATTER")
        return "format"
    
    # Check if report passed (handle both dict and legacy string formats)
    if isinstance(critique, dict):
        decision = critique.get('decision', 'PASS').upper()
        passed = decision == 'PASS'
    else:
        # Legacy string format fallback
        passed = "PASS" in str(critique).upper()
    
    if passed:
        logger.info(f"[DECISION] Report passed review, proceeding to FORMATTER")
        return "format"
    
    # Needs refinement
    logger.info(f"[DECISION] Report needs refinement (iteration {iterations + 1})")
    return "refine"


def create_analysis_graph() -> StateGraph:
    """
    Creates and configures the LangGraph workflow
    
    Graph Structure:
        START → COLLECTOR → ANALYZER → CRITIC → [REFINER] → [CRITIC] → FORMATTER → END
        
    The graph can loop between CRITIC and REFINER up to max_iterations times,
    then proceeds to FORMATTER to extract structured JSON before termination.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("[GRAPH] Building workflow")
    
    # Initialize graph with state schema
    workflow = StateGraph(AnalysisState)
    
    # Add nodes (A, B, C, D, E)
    workflow.add_node("collector", collector_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("refiner", refiner_node)
    workflow.add_node("formatter", formatter_node)  # Node E
    
    # Define edges
    workflow.set_entry_point("collector")
    workflow.add_edge("collector", "analyzer")
    workflow.add_edge("analyzer", "critic")
    
    # Conditional edge from critic
    workflow.add_conditional_edges(
        "critic",
        should_continue_refinement,
        {
            "format": "formatter",  # Go to formatter when done
            "refine": "refiner"
        }
    )
    
    # Loop back from refiner to critic
    workflow.add_edge("refiner", "critic")
    
    # Formatter is the final node before END
    workflow.add_edge("formatter", END)
    
    # Compile graph
    graph = workflow.compile()
    
    logger.info("[GRAPH] Compiled")
    return graph


async def execute_analysis(sector: str, country: str = "India") -> AnalysisState:
    """
    Main entry point for executing the LangGraph analysis workflow (async)
    
    This function initializes the state, creates the graph, and executes
    the complete workflow from data collection through quality validation.
    Uses ainvoke for async node support.
    
    Args:
        sector: The sector to analyze
        country: Target country (default: India)
        
    Returns:
        Final state containing the markdown report and metadata
    """
    logger.info(f"[WORKFLOW] Starting analysis for sector: {sector}")
    
    # Initialize state with current timestamp
    now_iso = datetime.utcnow().isoformat()
    initial_state: AnalysisState = {
        "sector": sector,
        "country": country,
        "raw_data": None,
        "search_results": None,
        "markdown_report": None,
        "critique": None,
        "iterations": 0,
        "error": None,
        "timestamp": now_iso,
        "json_summary": None
    }
    
    # Create and execute graph (async)
    try:
        graph = create_analysis_graph()
        final_state = await graph.ainvoke(initial_state)
        
        logger.info(
            f"[WORKFLOW] ✓ Completed in {final_state['iterations']} refinement iterations"
        )
        return final_state
        
    except Exception as e:
        logger.error(f"[WORKFLOW] Fatal error: {e}")
        initial_state['error'] = f"Workflow execution failed: {str(e)}"
        initial_state['markdown_report'] = _generate_error_report(sector, country, str(e))
        return initial_state


def _generate_error_report(sector: str, country: str, error: str) -> str:
    """Generate error report when workflow fails"""
    return f"""# {sector.title()} Sector - Trade Opportunities Analysis ({country})

## Workflow Error

The analysis workflow encountered a critical error and could not complete.

**Error Details:**
```
{error}
```

## Recommended Actions

1. Verify API configuration
2. Check internet connection
3. Review application logs
4. Try again or contact support

*Sector: {sector.title()} | Market: {country} | Status: Error*
"""
