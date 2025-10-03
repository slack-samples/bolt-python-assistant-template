from logging import Logger
from slack_sdk import WebClient
from slack_bolt import Say

from ai.llm_caller import call_llm
from ..views.feedback_block import create_feedback_block

"""
Handles the event when the app is mentioned in a Slack conversation
and generates an AI response.
"""


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
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

        returned_message = call_llm([{"role": "user", "content": text}])

        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
        )

        # Loop over OpenAI response stream
        # https://platform.openai.com/docs/api-reference/responses/create
        for event in returned_message:
            if event.type == "response.output_text.delta":
                streamer.append(markdown_text=f"{event.delta}")
            else:
                continue

        feedback_block = create_feedback_block()
        streamer.stop(blocks=feedback_block)
    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
