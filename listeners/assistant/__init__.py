from slack_bolt import App, Assistant

from .assistant_thread_started import start_assistant_thread
from .message import respond_in_assistant_thread


# Refer to https://tools.slack.dev/bolt-python/concepts/assistant/ for more details on the Assistant class
def register(app: App):
    assistant = Assistant()

    assistant.thread_started(start_assistant_thread)
    assistant.user_message(respond_in_assistant_thread)

    app.assistant(assistant)
