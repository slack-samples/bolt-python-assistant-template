import logging
from typing import Dict, List

from slack_bolt import Assistant, BoltContext, Say, SetStatus, SetSuggestedPrompts
from slack_bolt.context.get_thread_context import GetThreadContext
from slack_sdk import WebClient

from ..llm_caller import call_llm

# Refer to https://tools.slack.dev/bolt-python/concepts/assistant/ for more details
assistant = Assistant()


# This listener is invoked when a human user opened an assistant thread
@assistant.thread_started
def start_assistant_thread(
    say: Say,
    get_thread_context: GetThreadContext,
    set_suggested_prompts: SetSuggestedPrompts,
    logger: logging.Logger,
):
    try:
        say("How can I help you?")

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

        thread_context = get_thread_context()
        if thread_context is not None and thread_context.channel_id is not None:
            summarize_channel = {
                "title": "Summarize the referred channel",
                "message": "Can you generate a brief summary of the referred channel?",
            }
            prompts.append(summarize_channel)

        set_suggested_prompts(prompts=prompts)
    except Exception as e:
        logger.exception(f"Failed to handle an assistant_thread_started event: {e}", e)
        say(f":warning: Something went wrong! ({e})")


# This listener is invoked when the human user sends a reply in the assistant thread
@assistant.user_message
def respond_in_assistant_thread(
    client: WebClient,
    context: BoltContext,
    logger: logging.Logger,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    try:
        channel_id = payload["channel"]
        thread_ts = payload["thread_ts"]

        loading_messages = [
            "Teaching the hamsters to type faster…",
            "Untangling the internet cables…",
            "Consulting the office goldfish…",
            "Polishing up the response just for you…",
            "Convincing the AI to stop overthinking…",
        ]

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
        set_status(
            status="Bolt is typing",
            loading_messages=loading_messages,
        )
        stream_response = client.chat_startStream(
            channel=channel_id,
            thread_ts=thread_ts,
        )
        stream_ts = stream_response["ts"]
        # use of this for loop is specific to openai response method
        for event in returned_message:
            if event.type == "response.output_text.delta":
                client.chat_appendStream(channel=channel_id, ts=stream_ts, markdown_text=f"{event.delta}")
            else:
                continue

        client.chat_stopStream(
            channel=channel_id,
            ts=stream_ts,
        )

    except Exception as e:
        logger.exception(f"Failed to handle a user message event: {e}")
        say(f":warning: Something went wrong! ({e})")
