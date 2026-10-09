"""Depth-limited minimax with alpha-beta pruning.

The rules package is still a stub in this repository, so legal action
generation and state transitions are injected by the caller. ``apply_action``
must return a new state (or an independent copy); search must not mutate its
parent states.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Hashable
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Generic, TypeVar

from ..game.state import GameState
from .evaluator import Evaluator, evaluate


ActionT = TypeVar("ActionT")
ActionGenerator = Callable[[GameState], Iterable[ActionT]]
Transition = Callable[[GameState, ActionT], GameState]


@dataclass(frozen=True, slots=True)
class DecisionResult(Generic[ActionT]):
    """Chosen action and its estimated utility."""

    action: ActionT
    value: float
    depth: int
    nodes_searched: int
    transposition_hits: int = 0


@dataclass(frozen=True, slots=True)
class _TableEntry:
    value: float
    bound: str  # exact, lower, or upper


def _freeze(value: object) -> Hashable:
    """Build a stable hashable key from the project's dataclass game state."""
    if isinstance(value, Enum):
        return (type(value).__qualname__, _freeze(value.value))
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return (
            type(value).__qualname__,
            tuple((item.name, _freeze(getattr(value, item.name))) for item in fields(value)),
        )
    if isinstance(value, dict):
        return tuple(sorted(((_freeze(k), _freeze(v)) for k, v in value.items()), key=repr))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item) for item in value), key=repr))
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


class MinimaxDecisionEngine(Generic[ActionT]):
    """Choose an action using minimax and alpha-beta pruning.

    Depth counts individual player actions. This is a perfect-information
    search over the supplied state model; hidden-information handling must be
    done by the caller (for example by sampling possible opponent hands).
    """

    def __init__(self, depth: int = 4, evaluator: Evaluator = evaluate) -> None:
        if depth < 1:
            raise ValueError("depth must be at least 1")
        self.depth = depth
        self.evaluator = evaluator
        self.nodes_searched = 0
        self.transposition_hits = 0
        self._transpositions: dict[tuple[Hashable, int], _TableEntry] = {}

    def choose(
        self,
        state: GameState,
        legal_actions: ActionGenerator[ActionT],
        apply_action: Transition[ActionT],
    ) -> DecisionResult[ActionT]:
        """Return the best current action; ties follow generator order."""
        actions = tuple(legal_actions(state))
        if not actions:
            raise ValueError("cannot choose an action: no legal actions")

        self.nodes_searched = 0
        self.transposition_hits = 0
        self._transpositions.clear()
        maximizing = state.turn.is_your_turn
        children = [(action, apply_action(state, action)) for action in actions]
        children.sort(
            key=lambda pair: self.evaluator(pair[1]),
            reverse=maximizing,
        )
        best_action = children[0][0]
        best_value = float("-inf") if maximizing else float("inf")
        alpha, beta = float("-inf"), float("inf")

        for action, child in children:
            value = self._search(child, self.depth - 1, alpha, beta, legal_actions, apply_action)
            if (maximizing and value > best_value) or (not maximizing and value < best_value):
                best_action, best_value = action, value
            if maximizing:
                alpha = max(alpha, best_value)
            else:
                beta = min(beta, best_value)

        return DecisionResult(
            best_action, best_value, self.depth, self.nodes_searched,
            self.transposition_hits,
        )

    def _search(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        legal_actions: ActionGenerator[ActionT],
        apply_action: Transition[ActionT],
    ) -> float:
        self.nodes_searched += 1
        if depth <= 0 or state.is_game_over():
            return self.evaluator(state)

        key = (_freeze(state), depth)
        original_alpha, original_beta = alpha, beta
        cached = self._transpositions.get(key)
        if cached is not None:
            self.transposition_hits += 1
            if cached.bound == "exact":
                return cached.value
            if cached.bound == "lower":
                alpha = max(alpha, cached.value)
            else:
                beta = min(beta, cached.value)
            if alpha >= beta:
                return cached.value

        actions = tuple(legal_actions(state))
        if not actions:
            # A state with no generated actions is treated as a leaf. The game
            # rules should model pass/draw explicitly if either is available.
            return self.evaluator(state)

        maximizing = state.turn.is_your_turn
        children = [(action, apply_action(state, action)) for action in actions]
        children.sort(
            key=lambda pair: self.evaluator(pair[1]),
            reverse=maximizing,
        )
        if maximizing:
            value = float("-inf")
            for _action, child in children:
                value = max(
                    value,
                    self._search(
                        child, depth - 1, alpha, beta,
                        legal_actions, apply_action,
                    ),
                )
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = float("inf")
            for _action, child in children:
                value = min(
                    value,
                    self._search(
                        child, depth - 1, alpha, beta,
                        legal_actions, apply_action,
                    ),
                )
                beta = min(beta, value)
                if alpha >= beta:
                    break

        if value <= original_alpha:
            bound = "upper"
        elif value >= original_beta:
            bound = "lower"
        else:
            bound = "exact"
        self._transpositions[key] = _TableEntry(value, bound)
        return value


def choose_action(
    state: GameState,
    legal_actions: ActionGenerator[ActionT],
    apply_action: Transition[ActionT],
    *,
    depth: int = 4,
    evaluator: Evaluator = evaluate,
) -> DecisionResult[ActionT]:
    """Convenience function for a one-shot minimax decision."""
    return MinimaxDecisionEngine[ActionT](depth, evaluator).choose(
        state, legal_actions, apply_action
    )
