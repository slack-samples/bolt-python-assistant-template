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

        set_status(
            status="thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

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

        returned_message = call_llm(messages_in_thread)

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
