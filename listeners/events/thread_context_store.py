from typing import Optional
from slack_sdk import WebClient
from slack_bolt import BoltContext


def _find_parent_message(
    *,
    context: BoltContext,
    client: WebClient,
    channel_id: str,
    thread_ts: str,
) -> Optional[dict]:
    response = client.conversations_replies(
        channel=channel_id,
        ts=thread_ts,
        oldest=thread_ts,
        include_all_metadata=True,
        limit=4,
    )
    if response.get("messages"):
        for message in response.get("messages"):
            if message.get("subtype") is None and message.get("user") == context.bot_user_id:
                return message


def get_thread_context(
    *,
    context: BoltContext,
    client: WebClient,
    channel_id: str,
    thread_ts: str,
) -> Optional[dict]:
    parent_message = _find_parent_message(context=context, client=client, channel_id=channel_id, thread_ts=thread_ts)
    if parent_message is not None and parent_message.get("metadata") is not None:
        return parent_message["metadata"]["event_payload"]


def save_thread_context(
    *,
    context: BoltContext,
    client: WebClient,
    channel_id: str,
    thread_ts: str,
    new_context: dict,
) -> None:
    parent_message = _find_parent_message(
        context=context,
        client=client,
        channel_id=channel_id,
        thread_ts=thread_ts,
    )
    if parent_message is not None:
        client.chat_update(
            channel=channel_id,
            ts=parent_message["ts"],
            text=parent_message["text"],
            blocks=parent_message.get("blocks"),
            metadata={
                "event_type": "assistant_thread_context",
                "event_payload": new_context,
            },
        )
