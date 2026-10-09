"""Public evaluator entry point used by search and other strategies."""

from __future__ import annotations

from collections.abc import Callable

from ..game.state import GameState
from .heuristics import evaluate_position


Evaluator = Callable[[GameState], float]


def evaluate(state: GameState) -> float:
    """Return a scalar utility from our perspective; higher is better."""
    return evaluate_position(state)


class StateEvaluator:
    """Callable wrapper that can be injected into the decision engine."""

    def __call__(self, state: GameState) -> float:
        return evaluate(state)
