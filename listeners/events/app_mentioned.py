from logging import Logger

from openai.types.responses import ResponseInputParam
from slack_bolt import Say
from slack_sdk import WebClient

from agent.llm_caller import call_llm
from listeners.views.feedback_block import create_feedback_block


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    """
    Handles the event when the app is mentioned in a Slack conversation
    and generates an AI response.

    Args:
        client: Slack WebClient for making API calls
        event: Event payload containing mention details (channel, user, text, etc.)
        logger: Logger instance for error tracking
        say: Function to send messages to the thread from the app
    """
    try:
        channel_id = event.get("channel")
        team_id = event.get("team")
        text = event.get("text")
        thread_ts = event.get("thread_ts") or event.get("ts")
        user_id = event.get("user")

        client.assistant_threads_setStatus(
            channel_id=channel_id,
            thread_ts=thread_ts,
            status="thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
        )
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
