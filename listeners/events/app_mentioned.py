from logging import Logger
from slack_sdk import WebClient
from slack_bolt import Say
from slack_bolt.context.get_thread_context import GetThreadContext
from typing import List, Dict

from ..llm_caller import call_llm
from ..views.feedback_block import create_feedback_block
from ..listeners_constants import loading_messages

"""
Handles the event when the app is mentioned in a Slack channel, retrieves the conversation context,
and generates an AI response if text is provided, otherwise sends a default response
"""


def app_mentioned_callback(
    client: WebClient, event: dict, logger: Logger, say: Say
):
    try:

        channel_id = event.get("channel")
        thread_ts = event.get("thread_ts")
        user_id = event.get("user")
        team_id = event.get("team")
        text = event.get("text")

        if thread_ts:
            conversation_context = client.conversations_replies(channel=channel_id, ts=thread_ts, limit=10)
        else:
            conversation_context = client.conversations_history(channel=channel_id, limit=50)
            thread_ts = event["ts"]

        messages_in_thread: List[Dict[str, str]] = []
        for message in conversation_context["messages"]:
            role = "user" if message.get("bot_id") is None else "assistant"
            messages_in_thread.append({"role": role, "content": message["text"]})
        if text:
            returned_message = call_llm(messages_in_thread)

        client.assistant_threads_setStatus(
            channel_id=channel_id, thread_ts=thread_ts, status="Bolt is typing", loading_messages=loading_messages
        )
        stream_response = client.chat_startStream(
            channel=channel_id, recipient_team_id=team_id, recipient_user_id=user_id, thread_ts=thread_ts
        )

        stream_ts = stream_response["ts"]

        # use of this for loop is specific to openai response method
        for event in returned_message:
            if event.type == "response.output_text.delta":
                client.chat_appendStream(channel=channel_id, ts=stream_ts, markdown_text=f"{event.delta}")
            else:
                continue

        feedback_block = create_feedback_block()
        client.chat_stopStream(channel=channel_id, ts=stream_ts, blocks=feedback_block)

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
