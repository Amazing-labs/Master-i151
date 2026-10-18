"""Master-i151 — competition entry point (SDK contract: setup / decide / observe).

The logic lives in the sibling modules (the SDK only loads flat modules next
to bot.py): see decision_service.py for the pipeline.
"""

from decision_service import DecisionService

_service = DecisionService()


def setup(submission_dir):
    """Called once before each match."""
    del submission_dir
    _service.reset()


def observe(view):
    """Called after every opponent action. Knowledge only: never fatal."""
    try:
        _service.observe(view)
    except Exception:
        pass


def decide(view, legal_actions, time_left_ms):
    """Return one of `legal_actions`."""
    del time_left_ms
    return _service.decide(view, legal_actions)
