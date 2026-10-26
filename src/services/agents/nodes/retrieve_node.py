import logging
import time
from typing import Dict, Union

from langchain_core.messages import AIMessage
from langgraph.runtime import Runtime

from ..context import Context
from ..state import AgentState
from .utils import get_latest_query

logger = logging.getLogger(__name__)


async def ainvoke_retrieve_step(
    state: AgentState,
    runtime: Runtime[Context],
) -> Dict[str, Union[int, str, list]]:
    """Initiate retrieval or return fallback if max attempts reached.

    This node creates a tool call to retrieve documents, or returns a fallback
    message if the maximum number of retrieval attempts has been reached.

    :param state: Current agent state
    :param runtime: Runtime context containing max_retrieval_attempts
    :returns: Dictionary with updated state (retrieval_attempts, messages, original_query)
    """
    logger.info("NODE: retrieve")
    start_time = time.time()

    messages = state["messages"]
    question = get_latest_query(messages)
    current_attempts = state.get("retrieval_attempts", 0)

    # Get max attempts from context
    max_attempts = runtime.context.max_retrieval_attempts

    # Store original query if not set
    updates = {}
    if state.get("original_query") is None:
        updates["original_query"] = question
        logger.debug(f"Stored original query: {question[:100]}...")

    # Check if max attempts reached
    if current_attempts >= max_attempts:
        logger.warning(f"Max retrieval attempts ({max_attempts}) reached")
        fallback_msg = (
            f"I apologize, but I couldn't find relevant research papers after {max_attempts} attempts.\n"
            "This may be because:\n"
            "1. No papers in the database contain relevant information\n"
            "2. The query terms don't match the indexed content\n\n"
            "Please try rephrasing your question with more specific technical terms."
        )

        return {**updates, "messages": [AIMessage(content=fallback_msg)]}

    # Increment retrieval attempts
    new_attempt_count = current_attempts + 1
    updates["retrieval_attempts"] = new_attempt_count
    logger.info(f"Retrieval attempt {new_attempt_count}/{max_attempts}")

    # Create tool call for retrieval
    updates["messages"] = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "id": f"retrieve_{new_attempt_count}",
                    "name": "retrieve_papers",
                    "args": {"query": question},
                }
            ],
        )
    ]

    logger.debug(f"Created tool call for query: {question[:100]}...")

    return updates
