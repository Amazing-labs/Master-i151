from __future__ import annotations

import unittest

from src.domain.game.cards import Card, Rank, Suit
from src.domain.game.state import GameState
from src.domain.strategy.evaluator import StateEvaluator, evaluate
from src.domain.strategy.scoring import (
    ELIMINATION_SCORE,
    WIN_SCORE,
    elimination_margin,
    hand_points,
    hand_size,
    terminal_value,
)


class ScoringTests(unittest.TestCase):
    def test_hand_points_and_size(self) -> None:
        cards = [Card(Rank.EIGHT, Suit.HEARTS), Card(Rank.JACK, Suit.CLUBS)]
        self.assertEqual(hand_points(cards), 34)
        self.assertEqual(hand_size(cards), 2)
        self.assertEqual(hand_points([]), 0)

    def test_elimination_margin_uses_configured_target(self) -> None:
        self.assertEqual(elimination_margin(100), 51)
        self.assertEqual(elimination_margin(160), -9)
        self.assertEqual(elimination_margin(6, target_score=10), 4)

    def test_terminal_value_rewards_opponent_elimination(self) -> None:
        self.assertEqual(terminal_value(20, ELIMINATION_SCORE), WIN_SCORE)
        self.assertEqual(terminal_value(ELIMINATION_SCORE, 20), -WIN_SCORE)
        self.assertIsNone(terminal_value(20, 30))

    def test_both_eliminated_prefers_lower_score(self) -> None:
        self.assertEqual(terminal_value(151, 160), WIN_SCORE)
        self.assertEqual(terminal_value(160, 151), -WIN_SCORE)
        self.assertEqual(terminal_value(151, 151), 0.0)


class EvaluatorTests(unittest.TestCase):
    def test_cumulative_score_advantage_is_good_for_us(self) -> None:
        ahead = GameState()
        ahead.you.total_score = 20
        ahead.opponent.total_score = 80
        behind = GameState()
        behind.you.total_score = 80
        behind.opponent.total_score = 20
        self.assertGreater(evaluate(ahead), evaluate(behind))

    def test_our_high_point_hand_is_penalized(self) -> None:
        low_hand = GameState()
        high_hand = GameState()
        low_hand.you.hand_points = 2
        high_hand.you.hand_points = 32
        self.assertGreater(evaluate(low_hand), evaluate(high_hand))

    def test_does_not_use_hidden_opponent_hand_points(self) -> None:
        first = GameState()
        second = GameState()
        first.opponent.hand_size = second.opponent.hand_size = 4
        first.opponent.hand_points = 1
        second.opponent.hand_points = 100
        self.assertEqual(evaluate(first), evaluate(second))

    def test_evaluator_wrapper_matches_function(self) -> None:
        state = GameState()
        self.assertEqual(StateEvaluator()(state), evaluate(state))


if __name__ == "__main__":
    unittest.main()
