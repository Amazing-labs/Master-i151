"""Tunable weights of the strategy (values of bot V2.3).

Any change here must be validated with a paired benchmark
(scripts/benchmark.py, see docs/experiments.md).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Weights:
    # Play scoring: a sequence of cards played within one turn.
    per_card_played: int = 28
    per_point_dumped: int = 1
    per_card_remaining: int = -6
    empties_hand: int = 2_000
    finishes_on_queen: int = -10_000

    # Race: opponent close to going out.
    short_opponent_cards: int = 3
    race_per_card_played: int = 18
    race_per_card_remaining: int = -10

    # Race: we are close to going out.
    short_hand_cards: int = 4
    short_hand_per_card_played: int = 12

    # Queen in a duel: the opponent loses a turn.
    queen_skip_opponent_le_2: int = 55
    queen_skip_opponent_le_4: int = 35
    queen_skip_otherwise: int = 8
    single_queen_left: int = -40

    # Eight: keep it early, dump it late.
    eight_late: int = 40
    eight_late_remaining_cards: int = 2
    eight_big_hand_cards: int = 7
    eight_big_hand: int = -45
    eight_medium_hand_cards: int = 5
    eight_medium_hand: int = -25
    eight_small_hand: int = 5

    # Ace.
    ace_effect_already_active: int = -12
    ace_tactical: int = 18
    ace_short_opponent: int = 10

    # Suit choice after an eight.
    suit_per_card_in_hand: int = 3
    suit_per_card_on_table: float = 1.2
    suit_nearly_exhausted_cards: int = 7
    suit_nearly_exhausted: int = 2
    suit_absent_from_hand: int = -8


DEFAULT_WEIGHTS = Weights()
