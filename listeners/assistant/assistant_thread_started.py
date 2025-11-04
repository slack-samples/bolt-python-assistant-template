from logging import Logger
from typing import Dict, List

from slack_bolt import Say, SetSuggestedPrompts


def assistant_thread_started(
    say: Say,
    set_suggested_prompts: SetSuggestedPrompts,
    logger: Logger,
):
    """
    Handle the assistant thread start event by greeting the user and setting suggested prompts.

    Args:
        say: Function to send messages to the thread from the app
        set_suggested_prompts: Function to configure suggested prompt options
        logger: Logger instance for error tracking
    """
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

        set_suggested_prompts(prompts=prompts)
    except Exception as e:
        logger.exception(f"Failed to handle an assistant_thread_started event: {e}", e)
        say(f":warning: Something went wrong! ({e})")
