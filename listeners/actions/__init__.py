from slack_bolt import App

from .actions import handle_feedback


def register(app: App):
    app.action("feedback")(handle_feedback)
