from __future__ import annotations

import unittest

from src.domain.game.state import GameState
from src.domain.strategy.heuristics import evaluate_position
from src.domain.strategy.scoring import WIN_SCORE


class HeuristicTests(unittest.TestCase):
    def test_terminal_win_and_loss_override_heuristic(self) -> None:
        won = GameState()
        won.opponent.total_score = won.target_score
        lost = GameState()
        lost.you.total_score = lost.target_score
        self.assertEqual(evaluate_position(won), WIN_SCORE)
        self.assertEqual(evaluate_position(lost), -WIN_SCORE)

    def test_more_opponent_cards_improves_position(self) -> None:
        smaller_opponent_hand = GameState()
        larger_opponent_hand = GameState()
        smaller_opponent_hand.opponent.hand_size = 2
        larger_opponent_hand.opponent.hand_size = 5
        self.assertGreater(
            evaluate_position(larger_opponent_hand),
            evaluate_position(smaller_opponent_hand),
        )

    def test_turn_bonus_is_small_and_favors_our_turn(self) -> None:
        our_turn = GameState()
        opponent_turn = GameState()
        our_turn.turn.is_your_turn = True
        opponent_turn.turn.is_your_turn = False
        self.assertGreater(evaluate_position(our_turn), evaluate_position(opponent_turn))


if __name__ == "__main__":
    unittest.main()
