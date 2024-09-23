from slack_sdk import WebClient
from slack_bolt import BoltContext

from .thread_context_store import save_thread_context


def save_new_thread_context(
    payload: dict,
    client: WebClient,
    context: BoltContext,
):
    thread = payload["assistant_thread"]
    save_thread_context(
        context=context,
        client=client,
        channel_id=thread["channel_id"],
        thread_ts=thread["thread_ts"],
        new_context=thread.get("context"),
    )
