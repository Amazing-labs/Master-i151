"""Orchestration: PlayerView -> GameState -> knowledge -> strategy -> Action.

    view ──arena_adapter──> GameState ──> KnowledgeEngine.observe
    legal_actions ──actions (classification)──> strategy.Options
    StrategyEngine.decide ──> Decision (index) ──> legal Action
    validators.ensure_legal: final guard before returning to the SDK
"""

from __future__ import annotations

import random

import actions
import validators
from arena_adapter import action_cards, to_game_state, to_suit
from knowledge import KnowledgeEngine
from search import MonteCarloSearch
from strategy import Decision, DecisionKind, Options, StrategyEngine

# A round is forfeited past 3000 actions (500 in local runs). Searching bots
# may prefer drawing to playing, so long rounds fall back to the strategy,
# which always plays when it can.
MAX_SEARCH_ROUND_STEPS = 300


class DecisionService:
    def __init__(
        self,
        strategy: StrategyEngine | None = None,
        knowledge: KnowledgeEngine | None = None,
        search: MonteCarloSearch | None = None,
    ) -> None:
        self.strategy = strategy or StrategyEngine()
        self.knowledge = knowledge or KnowledgeEngine()
        self.search = search

    def reset(self) -> None:
        """New match: forget the previous one."""
        self.knowledge.reset()

    def observe(self, view) -> None:
        """Called by the SDK after every opponent action."""
        self.knowledge.observe(to_game_state(view), after_opponent_action=True)

    def decide(self, view, legal_actions: list):
        if not legal_actions:
            raise ValueError("The engine provided no legal action.")

        state = to_game_state(view)
        try:
            self.knowledge.observe(state)
        except Exception:
            # Knowledge is an aid: a bug there must not cost a forfeit.
            self.knowledge.reset()

        if (
            self.search is not None
            and len(legal_actions) > 1
            and self.knowledge.round_steps < MAX_SEARCH_ROUND_STEPS
        ):
            # Deterministic per state, so benchmarks are reproducible.
            rng = random.Random(state.round_number * 1_000_003 + state.step_index)
            try:
                index = self.search.choose(view, legal_actions, self.knowledge, rng)
            except Exception:
                index = None
            if index is not None:
                return validators.ensure_legal(legal_actions[index], legal_actions)

        suit_actions = actions.get_suit_choices(legal_actions)
        play_actions = actions.get_play_actions(legal_actions)
        pass_actions = actions.get_pass_actions(legal_actions)
        options = Options(
            suits=tuple(to_suit(action.chosen_suit) for action in suit_actions),
            plays=tuple(action_cards(action) for action in play_actions),
            can_pass=bool(pass_actions),
        )

        decision = self.strategy.decide(state, self.knowledge, options)
        chosen = _to_action(decision, legal_actions, suit_actions, play_actions, pass_actions)
        return validators.ensure_legal(chosen, legal_actions)


def _to_action(decision: Decision, legal_actions, suit_actions, play_actions, pass_actions):
    if decision.kind is DecisionKind.CHOOSE_SUIT:
        return suit_actions[decision.index]
    if decision.kind is DecisionKind.PLAY:
        return play_actions[decision.index]
    if decision.kind is DecisionKind.PASS:
        return pass_actions[0]
    return legal_actions[0]
