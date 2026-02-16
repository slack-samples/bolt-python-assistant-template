from logging import Logger

from slack_bolt import BoltAgent, Say


def assistant_thread_started(
    agent: BoltAgent,
    logger: Logger,
    say: Say,
):
    """
    Handle the assistant thread start event by greeting the user and setting suggested prompts.

    Args:
        say: Function to send messages to the thread from the app
        set_suggested_prompts: Function to configure suggested prompt options
        logger: Logger instance for error tracking
    """
    try:
        say("What would you like to do today?")
        agent.set_suggested_prompts(
            prompts=[
                {
                    "title": "Prompt a task with thinking steps",
                    "message": "Wonder a few deep thoughts.",
                },
                {
                    "title": "Roll dice for a random number",
                    "message": "Roll two 12-sided dice and three 6-sided dice for a pseudo-random score.",
                },
            ]
        )
    except Exception as e:
        logger.exception(f"Failed to handle an assistant_thread_started event: {e}", e)
        say(f":warning: Something went wrong! ({e})")
