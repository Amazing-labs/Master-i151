"""Heuristic features for evaluating a non-terminal game position."""

from __future__ import annotations

from ..game.state import GameState
from .scoring import terminal_value


def evaluate_position(state: GameState) -> float:
    """Estimate the position from our point of view (higher is better).

    Scores are penalty points, so being closer to 151 is bad for that player.
    Public opponent hand points/sizes are used only when supplied by the view;
    hidden cards are never reconstructed here.
    """
    target = state.target_score
    terminal = terminal_value(state.you.total_score, state.opponent.total_score, target)
    if terminal is not None:
        return terminal

    # A round loser adds the points left in their hand to their cumulative
    # score. Keeping fewer points is therefore directly useful.
    score_advantage = state.opponent.total_score - state.you.total_score
    # The opponent's cards are hidden. Do not use opponent.hand_points here:
    # the observation model must not turn an unknown hand into a known fact.
    # We can still use our own exact penalty points and the public hand sizes.
    hand_point_advantage = -state.you.hand_points
    hand_size_advantage = state.opponent.hand_size - state.you.hand_size

    # Give the accumulated score the most weight. Hand points matter strongly,
    # while hand size is a smaller proxy for how close each player is to going
    # out. This avoids treating a 32-point eight as interchangeable with a
    # low-point card simply because both count as one card.
    value = (
        4.0 * score_advantage
        + 1.0 * hand_point_advantage
        + 2.0 * hand_size_advantage
    )

    # Slightly prefer positions where the opponent is nearer the elimination
    # threshold. This term is deliberately small and cannot outweigh a large
    # hand-point swing.
    our_margin = max(0, target - state.you.total_score)
    opponent_margin = max(0, target - state.opponent.total_score)
    value += 0.15 * (our_margin - opponent_margin)

    # The turn belongs to the player who can act now; a tiny tempo bonus helps
    # break otherwise equal leaves without overriding the material features.
    if state.turn.is_your_turn:
        value += 0.25
    else:
        value -= 0.25

    return value
