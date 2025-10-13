from slack_bolt import App, Assistant

from .assistant_thread_started import start_assistant_thread
from .message import respond_in_assistant_thread


# Refer to https://docs.slack.dev/tools/bolt-python/concepts/ai-apps#assistant for more details on the Assistant class
def register(app: App):
    assistant = Assistant()

    assistant.thread_started(assistant_thread_started)
    assistant.user_message(message)

    app.assistant(assistant)
