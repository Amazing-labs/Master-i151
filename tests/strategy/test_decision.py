from __future__ import annotations

import copy
import unittest

from src.domain.game.state import GameState
from src.domain.strategy.decision import MinimaxDecisionEngine, choose_action
from src.domain.strategy.scoring import WIN_SCORE


def make_terminal_state(our_score: int, opponent_score: int) -> GameState:
    state = GameState()
    state.you.total_score = our_score
    state.opponent.total_score = opponent_score
    state.turn.is_your_turn = False
    return state


class MinimaxDecisionTests(unittest.TestCase):
    def test_chooses_action_that_eliminates_opponent(self) -> None:
        state = GameState()
        state.turn.is_your_turn = True
        actions = lambda _state: ("win", "lose")

        def apply(current: GameState, action: str) -> GameState:
            del current
            if action == "win":
                return make_terminal_state(10, 151)
            return make_terminal_state(151, 10)

        result = choose_action(state, actions, apply, depth=1)
        self.assertEqual(result.action, "win")
        self.assertEqual(result.value, WIN_SCORE)
        self.assertEqual(result.depth, 1)
        self.assertEqual(result.nodes_searched, 2)

    def test_opponent_node_minimizes_our_utility(self) -> None:
        root = GameState()
        root.step_index = 0
        root.turn.is_your_turn = True

        def actions(state: GameState) -> tuple[str, ...]:
            if state.step_index == 0:
                return ("safe", "risky")
            if state.step_index == 1:
                return ("opponent-good", "opponent-bad")
            return ()

        def apply(state: GameState, action: str) -> GameState:
            child = copy.deepcopy(state)
            child.step_index += 1
            child.turn.is_your_turn = not state.turn.is_your_turn
            if action == "safe":
                child.you.total_score = 10
                child.opponent.total_score = 20
            elif action == "risky":
                child.you.total_score = 10
                child.opponent.total_score = 21
            elif action == "opponent-good":
                child.opponent.total_score = 30
            elif action == "opponent-bad":
                child.you.total_score = 40 if state.opponent.total_score == 20 else 50
            return child

        result = MinimaxDecisionEngine[str](depth=2).choose(root, actions, apply)
        # The minimizing opponent can spoil either line, but the safe line has
        # the better worst-case cumulative score.
        self.assertEqual(result.action, "safe")

    def test_reuses_transposed_positions(self) -> None:
        root = GameState()
        root.turn.is_your_turn = True
        root.step_index = 0

        def actions(state: GameState) -> tuple[str, ...]:
            if state.step_index == 0:
                return ("left", "right")
            if state.step_index == 1:
                return ("continue",)
            return ()

        def apply(state: GameState, _action: str) -> GameState:
            child = copy.deepcopy(state)
            child.step_index += 1
            child.turn.is_your_turn = not child.turn.is_your_turn
            return child

        result = MinimaxDecisionEngine[str](depth=2).choose(root, actions, apply)
        self.assertEqual(result.transposition_hits, 1)

    def test_raises_if_no_root_action_exists(self) -> None:
        with self.assertRaises(ValueError):
            choose_action(GameState(), lambda _state: (), lambda state, _action: state)

    def test_requires_positive_search_depth(self) -> None:
        with self.assertRaises(ValueError):
            MinimaxDecisionEngine(depth=0)


if __name__ == "__main__":
    unittest.main()
