from .assistant import assistant


def register_listeners(app):
    app.assistant(assistant)
