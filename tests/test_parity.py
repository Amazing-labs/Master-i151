"""The strategy engine (bot/ without search) must take exactly the decisions of V2.3.

Both bots are loaded with the SDK loader, as in a real match, and play full
matches against medium. At every decision the two choices are compared.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest
from arena_sdk.loader import load_submission
from arena_sdk.opponents import resolve_opponent_arg
from i151_engine.runner.config import MatchConfig
from i151_engine.runner.match_runner import play_bots_match

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.integration


class _ParityBot:
    """The strategy alone (DecisionService without search) against V2.3."""

    def __init__(self) -> None:
        from decision_service import DecisionService

        self.new = DecisionService()
        self.reference = load_submission(ROOT / "archive" / "bots" / "bot_v2_3.py")
        self.decisions = 0

    def setup(self, submission_dir) -> None:
        self.new.reset()
        self.reference.setup(submission_dir)

    def observe(self, view) -> None:
        self.new.observe(view)

    def decide(self, view, legal_actions, time_left_ms):
        chosen = self.new.decide(view, legal_actions)
        expected = self.reference.decide(view, legal_actions, time_left_ms)
        assert chosen == expected, (view, legal_actions)
        self.decisions += 1
        return chosen

    def teardown(self) -> None:
        pass


def test_modular_bot_takes_the_same_decisions_as_v2_3():
    rng = random.Random(151)
    opponent = resolve_opponent_arg("medium")
    bot = _ParityBot()
    for game in range(60):
        result = play_bots_match(
            bot,
            opponent.bot,
            MatchConfig(seed=rng.randint(0, 2_000_000_000), initial_dealer_index=game % 2),
            opponent_id=opponent.opponent_id,
            manage_lifecycle=False,
        )
        assert result.reason == "normal", result
    assert bot.decisions > 10_000
