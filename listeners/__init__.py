from listeners import actions
from listeners import assistant


def register_listeners(app):

    actions.register(app)
    assistant.register(app)

    # The following event listeners demonstrate how to implement the same on your own.
    # from listeners import events
    # events.register(app)
