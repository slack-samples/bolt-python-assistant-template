from logging import Logger

from openai.types.responses import ResponseInputParam
from slack_bolt import BoltAgent, Say

from agent.llm_caller import call_llm
from listeners.views.feedback_block import create_feedback_block


def app_mentioned_callback(
    agent: BoltAgent,
    event: dict,
    logger: Logger,
    say: Say,
):
    """
    Handles the event when the app is mentioned in a Slack conversation
    and generates an AI response.

    Args:
        agent: BoltAgent for making API calls
        event: Event payload containing mention details (channel, user, text, etc.)
        logger: Logger instance for error tracking
        say: Function to send messages to the thread from the app
    """
    try:
        text = event.get("text")

        agent.set_status(
            status="thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        streamer = agent.chat_stream()
        prompts: ResponseInputParam = [
            {
                "role": "user",
                "content": text,
            },
        ]
        call_llm(streamer, prompts)

        feedback_block = create_feedback_block()
        streamer.stop(
            blocks=feedback_block,
        )
    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
