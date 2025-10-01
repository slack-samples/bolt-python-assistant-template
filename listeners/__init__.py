from listeners import actions
from listeners import assistant
from listeners import events


def register_listeners(app):
    actions.register(app)
    assistant.register(app)
    events.register(app)
