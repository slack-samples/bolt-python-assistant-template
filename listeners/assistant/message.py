import asyncio
from logging import Logger
from typing import Dict, List

from slack_bolt import BoltContext, Say, SetStatus
from slack_sdk import WebClient

from ai.llm_caller import call_llm

from ..views.feedback_block import create_feedback_block


def message(
    client: WebClient,
    context: BoltContext,
    logger: Logger,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    """
    Handles when users send messages or select a prompt in an assistant thread and generate AI responses:

    Args:
        client: Slack WebClient for making API calls
        context: Bolt context containing channel and thread information
        logger: Logger instance for error tracking
        payload: Event payload with message details (channel, user, text, etc.)
        say: Function to send messages to the thread
        set_status: Function to update the assistant's status
    """
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id

        # Set initial status - will be updated dynamically based on agent activity
        set_status(status="is thinking...")

        replies = client.conversations_replies(
            channel=context.channel_id,
            ts=context.thread_ts,
            oldest=context.thread_ts,
            limit=10,
        )
        messages_in_thread: List[Dict[str, str]] = []
        for message in replies["messages"]:
            role = "user" if message.get("bot_id") is None else "assistant"
            messages_in_thread.append({"role": role, "content": message["text"]})

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
                messages_in_thread, user_id=user_id, session_id=thread_ts
            ):
                if event["type"] == "status":
                    # Update the loading message with real-time agent activity
                    logger.info(f"Setting Slack loading message to: {event['text']}")
                    # Use client API directly to access loading_messages parameter
                    client.assistant_threads_setStatus(
                        channel_id=channel_id,
                        thread_ts=thread_ts,
                        status="is thinking...",  # The status below text box which typically shows "is typing..." for other users
                        loading_messages=[
                            event["text"]
                        ],  # The text that shows next to the app name shimmer. Here you can put custom text from you Agent events.
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
