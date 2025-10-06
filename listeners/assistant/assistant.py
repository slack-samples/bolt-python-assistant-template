import logging
from typing import Dict, List

from slack_bolt import Assistant, BoltContext, Say, SetStatus, SetSuggestedPrompts
from slack_bolt.context.get_thread_context import GetThreadContext
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..views.feedback_block import create_feedback_block
from ai.llm_caller import call_llm


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
    get_thread_context: GetThreadContext,
    logger: logging.Logger,
    payload: dict,
    say: Say,
    set_status: SetStatus,
):
    try:
        channel_id = payload["channel"]
        team_id = context.team_id
        thread_ts = payload["thread_ts"]
        user_id = context.user_id
        user_message = payload["text"]

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

        if user_message == "Can you generate a brief summary of the referred channel?":
            # the logic here requires the additional bot scopes:
            # channels:join, channels:history, groups:history
            thread_context = get_thread_context()
            referred_channel_id = thread_context.get("channel_id")
            try:
                channel_history = client.conversations_history(channel=referred_channel_id, limit=50)
            except SlackApiError as e:
                if e.response["error"] == "not_in_channel":
                    # If this app's bot user is not in the public channel,
                    # we'll try joining the channel and then calling the same API again
                    client.conversations_join(channel=referred_channel_id)
                    channel_history = client.conversations_history(channel=referred_channel_id, limit=50)
                else:
                    raise e
            prompt = f"Can you generate a brief summary of these messages in a Slack channel <#{referred_channel_id}>?\n\n"
            for message in reversed(channel_history.get("messages")):
                if message.get("user") is not None:
                    prompt += f"\n<@{message['user']}> says: {message['text']}\n"
            messages_in_thread = [{"role": "user", "content": prompt}]

        else:
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
