import asyncio
from logging import Logger

from slack_bolt import Say
from slack_sdk import WebClient

from ai.llm_caller import call_llm
from ..views.feedback_block import create_feedback_block


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

        # Set initial status with placeholder loading messages
        # Will be updated dynamically based on agent activity
        client.assistant_threads_setStatus(
            channel_id=channel_id,
            thread_ts=thread_ts,
            status="is thinking...",
            loading_messages=["Starting to process your request..."],
        )

        # Create event loop for async call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        streamer = client.chat_stream(
            channel=channel_id,
            recipient_team_id=team_id,
            recipient_user_id=user_id,
            thread_ts=thread_ts,
        )

        # Stream ADK response with dynamic status updates
        async def stream_response():
            async for event in call_llm(
                [{"role": "user", "content": text}],
                user_id=user_id,
                session_id=thread_ts,
            ):
                if event["type"] == "status":
                    # Update the loading message with real-time agent activity
                    # Keep generic status but show detailed info in loading_messages
                    logger.info(f"Setting Slack loading message to: {event['text']}")
                    client.assistant_threads_setStatus(
                        channel_id=channel_id,
                        thread_ts=thread_ts,
                        status="is working...",  # Generic status
                        loading_messages=[event["text"]],  # Specific detail
                    )
                elif event["type"] == "content":
                    # Stream the actual response content
                    if event["text"]:
                        streamer.append(markdown_text=event["text"])

        loop.run_until_complete(stream_response())
        loop.close()

        feedback_block = create_feedback_block()
        streamer.stop(blocks=feedback_block)
    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
