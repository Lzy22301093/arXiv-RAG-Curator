import logging
import time
from typing import Dict, Literal

from langgraph.runtime import Runtime

from ..context import Context
from ..models import GuardrailScoring
from ..prompts import GUARDRAIL_PROMPT
from ..state import AgentState
from .utils import get_latest_query

logger = logging.getLogger(__name__)


def continue_after_guardrail(state: AgentState, runtime: Runtime[Context]) -> Literal["continue", "out_of_scope"]:
    """Determine whether to continue or reject based on guardrail results.

    This function checks the guardrail_result score against a threshold.
    If the score is above threshold, continue; otherwise route to out_of_scope.

    :param state: Current agent state with guardrail results
    :param runtime: Runtime context containing guardrail threshold
    :returns: "continue" if score >= threshold, "out_of_scope" otherwise
    """
    guardrail_result = state.get("guardrail_result")
    if not guardrail_result:
        logger.warning("No guardrail result found, defaulting to continue")
        return "continue"

    score = guardrail_result.score
    threshold = runtime.context.guardrail_threshold

    logger.info(f"Guardrail score: {score}, threshold: {threshold}")

    return "continue" if score >= threshold else "out_of_scope"


async def ainvoke_guardrail_step(
    state: AgentState,
    runtime: Runtime[Context],
) -> Dict[str, GuardrailScoring]:
    """Asynchronously invoke the guardrail validation step using LLM.

    This function evaluates whether the user query is within scope
    (CS/AI/ML research papers) and assigns a score using an LLM.

    :param state: Current agent state
    :param runtime: Runtime context
    :returns: Dictionary with guardrail_result
    """
    logger.info("NODE: guardrail_validation")
    start_time = time.time()

    # Get the latest user query
    query = get_latest_query(state["messages"])
    logger.debug(f"Evaluating query: {query[:100]}...")

    try:
        # Create guardrail prompt from template
        guardrail_prompt = GUARDRAIL_PROMPT.format(question=query)

        # Get LLM from runtime context
        llm = runtime.context.get_llm(
            model=runtime.context.model_name,
            temperature=0.0,
        )

        # Create structured output LLM for guardrail scoring
        structured_llm = llm.with_structured_output(GuardrailScoring)

        # Invoke LLM for guardrail evaluation
        logger.info("Invoking LLM for guardrail validation")
        response = await structured_llm.ainvoke(guardrail_prompt)

        logger.info(f"Guardrail result - Score: {response.score}, Reason: {response.reason}")

    except Exception as e:
        logger.error(f"LLM guardrail validation failed: {e}, falling back to default")

        # Fallback to a conservative default if LLM fails
        response = GuardrailScoring(
            score=50,
            reason=f"LLM validation failed, using conservative default: {str(e)}"
        )

    return {"guardrail_result": response}
