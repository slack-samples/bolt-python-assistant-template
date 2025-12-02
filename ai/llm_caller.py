"""
LLM caller using Google ADK multi-agent system.

This module provides the interface for calling the ADK multi-agent system
and streaming responses back to Slack.
"""

import logging
from typing import Dict, List, AsyncGenerator, Literal

from google.adk.runners import InMemoryRunner
from google.genai import types

from .agents import get_root_agent

logger = logging.getLogger(__name__)


# Type for the events yielded by call_llm
class LLMEvent(Dict):
    """Event yielded during LLM processing."""

    type: Literal["status", "content"]
    text: str


# Initialize the ADK runner with the root agent
_runner = None
_app_name = "slack_ai_agent"


def get_adk_runner() -> InMemoryRunner:
    """Get or create the ADK InMemoryRunner instance."""
    global _runner
    if _runner is None:
        root_agent = get_root_agent()
        _runner = InMemoryRunner(agent=root_agent, app_name=_app_name)
    return _runner


async def call_llm(
    messages_in_thread: List[Dict[str, str]],
    user_id: str = "default_user",
    session_id: str = None,
) -> AsyncGenerator[Dict[str, str], None]:
    """
    Call the ADK multi-agent system and stream responses with status updates.

    Args:
        messages_in_thread: List of message dictionaries with 'role' and 'content' keys
        user_id: The Slack user ID
        session_id: Optional session ID for maintaining conversation context

    Yields:
        Dict[str, str]: Events with 'type' (either 'status' or 'content') and 'text' keys
            - status events: Updates about what the agent is doing (tool calls, agent transfers)
            - content events: Actual response text to display to the user
    """
    runner = get_adk_runner()

    # Create or get session
    if session_id is None:
        session_id = f"session_{user_id}"

    # Ensure session exists
    try:
        await runner.session_service.create_session(
            app_name=_app_name, user_id=user_id, session_id=session_id
        )
    except Exception:
        # Session might already exist, which is fine
        pass

    # Convert messages to ADK format - only send the last user message
    last_message = (
        messages_in_thread[-1]
        if messages_in_thread
        else {"role": "user", "content": ""}
    )

    # Create the message content
    new_message = types.Content(
        role="user", parts=[types.Part(text=last_message["content"])]
    )

    # Track the current agent for status updates
    current_agent = None
    has_started_streaming_content = False

    # Use the runner's run_async method for streaming
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_message
    ):
        # Log the full event for debugging
        logger.info(
            f"ADK Event - Author: {event.author}, Has content: {bool(event.content)}"
        )
        logger.info(f"Event attributes: {dir(event)}")

        # Detect agent changes/transfers
        if event.author and event.author != "user" and event.author != current_agent:
            current_agent = event.author
            # Only show agent status before we start streaming actual content
            if not has_started_streaming_content:
                status_text = f"{current_agent} is working..."
                logger.info(f"Yielding status: {status_text}")
                yield {"type": "status", "text": status_text}

        # Detect tool calls (function calls)
        function_calls = (
            event.get_function_calls() if hasattr(event, "get_function_calls") else []
        )
        logger.info(f"Function calls detected: {len(function_calls)}")
        if function_calls and not has_started_streaming_content:
            for func_call in function_calls:
                tool_name = (
                    func_call.name if hasattr(func_call, "name") else str(func_call)
                )
                # Make tool names more readable
                readable_name = tool_name.replace("_", " ").title()
                status_text = f"Using {readable_name}..."
                logger.info(f"Yielding tool status: {status_text}")
                yield {"type": "status", "text": status_text}

        # Detect agent transfers
        if hasattr(event, "actions") and event.actions:
            logger.info(f"Event has actions: {event.actions}")
            if (
                hasattr(event.actions, "transfer_to_agent")
                and event.actions.transfer_to_agent
            ):
                target_agent = event.actions.transfer_to_agent
                status_text = f"Consulting {target_agent}..."
                logger.info(f"Yielding transfer status: {status_text}")
                yield {"type": "status", "text": status_text}

        # Stream all non-user content events
        if event.content and event.content.parts and event.author != "user":
            # Extract text from all parts and yield as content
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    has_started_streaming_content = True
                    yield {"type": "content", "text": part.text}
