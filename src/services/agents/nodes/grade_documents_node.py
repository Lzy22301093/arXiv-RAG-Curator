import logging
import time
from typing import Dict

from langgraph.runtime import Runtime

from ..context import Context
from ..models import GradeDocuments, GradingResult
from ..prompts import GRADE_DOCUMENTS_PROMPT
from ..state import AgentState
from .utils import get_latest_context, get_latest_query

logger = logging.getLogger(__name__)


async def ainvoke_grade_documents_step(
    state: AgentState,
    runtime: Runtime[Context],
) -> Dict[str, str | list]:
    """Grade retrieved documents for relevance using LLM.

    This function uses an LLM to evaluate whether the retrieved documents
    are relevant to the user's query and decides whether to generate an
    answer or rewrite the query for better results.

    :param state: Current agent state
    :param runtime: Runtime context
    :returns: Dictionary with routing_decision and grading_results
    """
    logger.info("NODE: grade_documents")
    start_time = time.time()

    # Get query and context
    question = get_latest_query(state["messages"])
    context = get_latest_context(state["messages"])

    if not context:
        logger.warning("No context found, routing to rewrite_query")
        return {"routing_decision": "rewrite_query", "grading_results": []}

    logger.debug(f"Grading context of length {len(context)} characters")

    # Use LLM to grade document relevance
    try:
        # Create grading prompt from template
        grading_prompt = GRADE_DOCUMENTS_PROMPT.format(
            context=context,
            question=question,
        )

        # Get LLM from runtime context
        llm = runtime.context.get_llm(
            model=runtime.context.model_name,
            temperature=0.0,
        )

        # Create structured output LLM for grading
        structured_llm = llm.with_structured_output(GradeDocuments)

        # Invoke LLM grading
        logger.info("Invoking LLM for document grading")
        grading_response = await structured_llm.ainvoke(grading_prompt)

        is_relevant = grading_response.binary_score == "yes"
        score = 1.0 if is_relevant else 0.0

        logger.info(f"LLM grading: score={grading_response.binary_score}, reasoning={grading_response.reasoning}")

        # Create grading result record
        grading_result = GradingResult(
            document_id="retrieved_docs",
            is_relevant=is_relevant,
            score=score,
            reasoning=grading_response.reasoning,
        )

    except Exception as e:
        logger.error(f"LLM grading failed: {e}, falling back to heuristic")
        # Fallback to simple heuristic if LLM fails
        is_relevant = len(context.strip()) > 50
        grading_result = GradingResult(
            document_id="retrieved_docs",
            is_relevant=is_relevant,
            score=1.0 if is_relevant else 0.0,
            reasoning=f"Fallback heuristic (LLM failed): {'sufficient content' if is_relevant else 'insufficient content'}",
        )

    # Determine routing
    route = "generate_answer" if is_relevant else "rewrite_query"

    logger.info(f"Grading result: {'relevant' if is_relevant else 'not relevant'}, routing to: {route}")

    return {
        "routing_decision": route,
        "grading_results": [grading_result],
    }
