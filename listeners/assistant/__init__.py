from slack_bolt import App

from .assistant import assistant


def register(app: App):
    app.assistant(assistant)
