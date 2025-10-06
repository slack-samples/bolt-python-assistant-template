from typing import List, Dict
from logging import Logger

from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
from slack_bolt import BoltContext
from ..llm_caller import call_llm
from .thread_context_store import get_thread_context


def respond_to_user_message(
    payload: dict,
    client: WebClient,
    context: BoltContext,
    logger: Logger,
):
    channel_id, thread_ts = payload["channel"], payload["thread_ts"]
    try:
        user_message = payload["text"]
        thread_context = get_thread_context(
            context=context,
            client=client,
            channel_id=channel_id,
            thread_ts=thread_ts,
        )

        client.assistant_threads_setStatus(
            channel_id=channel_id,
            thread_ts=thread_ts,
            status="is typing...",
        )
        if user_message == "Can you generate a brief summary of the referred channel?":
            # the logic here requires the additional bot scopes:
            # channels:join, channels:history, groups:history
            referred_channel_id = thread_context.get("channel_id")
            try:
                channel_history = client.conversations_history(
                    channel=referred_channel_id,
                    limit=50,
                )
            except SlackApiError as e:
                if e.response["error"] == "not_in_channel":
                    # If this app's bot user is not in the public channel,
                    # we'll try joining the channel and then calling the same API again
                    client.conversations_join(channel=referred_channel_id)
                    channel_history = client.conversations_history(
                        channel=referred_channel_id,
                        limit=50,
                    )
                else:
                    raise e

            prompt = f"Can you generate a brief summary of these messages in a Slack channel <#{referred_channel_id}>?\n\n"
            for message in reversed(channel_history.get("messages")):
                if message.get("user") is not None:
                    prompt += f"\n<@{message['user']}> says: {message['text']}\n"
            messages_in_thread = [{"role": "user", "content": prompt}]
            returned_message = call_llm(messages_in_thread)
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=returned_message,
            )
            return

        replies = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            oldest=thread_ts,
            limit=10,
        )
        messages_in_thread: List[Dict[str, str]] = []
        for message in replies["messages"]:
            role = "user" if message.get("bot_id") is None else "assistant"
            messages_in_thread.append({"role": role, "content": message["text"]})
        returned_message = call_llm(messages_in_thread)
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=returned_message,
        )
    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f":warning: Something went wrong! ({e})",
        )
