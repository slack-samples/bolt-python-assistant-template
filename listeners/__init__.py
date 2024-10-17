from .assistant import assistant


def register_listeners(app):
    # Using assistant middleware is the recommended way.
    app.assistant(assistant)

    # The following event listeners demonstrate how to implement the same on your own.
    # from listeners import events
    # events.register(app)
