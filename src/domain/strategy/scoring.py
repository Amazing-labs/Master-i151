"""Small, reusable scoring functions for the i151 strategy."""

from __future__ import annotations

from collections.abc import Iterable

from ..game.cards import Card


# The game ends when either player reaches this many penalty points.
ELIMINATION_SCORE = 151

# Terminal values must dominate all non-terminal heuristic values.
WIN_SCORE = 1_000_000


def hand_points(cards: Iterable[Card]) -> int:
    """Return the penalty points currently held in ``cards``."""
    return sum(card.points for card in cards)


def hand_size(cards: Iterable[Card]) -> int:
    """Return the number of cards in a hand."""
    return sum(1 for _ in cards)


def elimination_margin(total_score: int, target_score: int = ELIMINATION_SCORE) -> int:
    """Return how many points remain before elimination (negative if eliminated)."""
    return target_score - total_score


def terminal_value(
    our_score: int,
    opponent_score: int,
    target_score: int = ELIMINATION_SCORE,
) -> float | None:
    """Return a decisive utility for a finished game, otherwise ``None``.

    The player who reaches the target loses. If malformed input says both
    players reached it, the lower score wins; an exact tie is a draw.
    """
    our_out = our_score >= target_score
    opponent_out = opponent_score >= target_score
    if not our_out and not opponent_out:
        return None
    if our_out and not opponent_out:
        return -WIN_SCORE
    if opponent_out and not our_out:
        return WIN_SCORE
    if our_score < opponent_score:
        return WIN_SCORE
    if opponent_score < our_score:
        return -WIN_SCORE
    return 0.0
