from typing import List

from slack_sdk.models.blocks import (
    Block,
    ContextActionsBlock,
    FeedbackButtonObject,
    FeedbackButtonsElement,
)


def create_feedback_block() -> List[Block]:
    """
    Create feedback block with thumbs up/down buttons

    Returns:
        Block Kit context_actions block
    """
    blocks: List[Block] = [
        ContextActionsBlock(
            elements=[
                FeedbackButtonsElement(
                    action_id="feedback",
                    positive_button=FeedbackButtonObject(
                        text="Good Response",
                        accessibility_label="Submit positive feedback on this response",
                        value="good-feedback",
                    ),
                    negative_button=FeedbackButtonObject(
                        text="Bad Response",
                        accessibility_label="Submit negative feedback on this response",
                        value="bad-feedback",
                    ),
                )
            ]
        )
    ]
    return blocks
