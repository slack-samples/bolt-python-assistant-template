from typing import List, Dict
from logging import Logger

from slack_sdk import WebClient


def start_thread_with_suggested_prompts(
    payload: dict,
    client: WebClient,
    logger: Logger,
):
    thread = payload["assistant_thread"]
    channel_id, thread_ts = thread["channel_id"], thread["thread_ts"]
    try:
        thread_context = thread.get("context")
        message_metadata = (
            {
                "event_type": "assistant_thread_context",
                "event_payload": thread_context,
            }
            if bool(thread_context) is True  # the dict is not empty
            else None
        )
        client.chat_postMessage(
            text="How can I help you?",
            channel=channel_id,
            thread_ts=thread_ts,
            metadata=message_metadata,
        )

        prompts: List[Dict[str, str]] = [
            {
                "title": "What does Slack stand for?",
                "message": "Slack, a business communication service, was named after an acronym. Can you guess what it stands for?",
            },
            {
                "title": "Write a draft announcement",
                "message": "Can you write a draft announcement about a new feature my team just released? It must include how impactful it is.",
            },
            {
                "title": "Suggest names for my Slack app",
                "message": "Can you suggest a few names for my Slack app? The app helps my teammates better organize information and plan priorities and action items.",
            },
        ]
        if message_metadata is not None:
            prompts.append(
                {
                    "title": "Summarize the referred channel",
                    "message": "Can you generate a brief summary of the referred channel?",
                }
            )

        client.assistant_threads_setSuggestedPrompts(
            channel_id=channel_id,
            thread_ts=thread_ts,
            prompts=prompts,
        )
    except Exception as e:
        logger.exception(f"Failed to handle an assistant_thread_started event: {e}", e)
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f":warning: Something went wrong! ({e})",
        )
