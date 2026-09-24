from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .cards import Card, Suit


@dataclass(slots=True)
class PlayerState:
    """
    State of one player as observable by the bot.

    Important distinction:

        hand_points
            Value of the cards currently held in the hand.

        total_score
            Cumulative score for the current game.
    """

    hand: list[Card] = field(default_factory=list)

    hand_points: int = 0

    total_score: int = 0

    hand_size: int = 0

    is_chaining: bool = False

    consecutive_round_wins: int = 0

    def update_hand(self, hand: list[Card]) -> None:
        self.hand = list(hand)
        self.hand_size = len(self.hand)
        self.hand_points = sum(card.points for card in self.hand)


@dataclass(slots=True)
class TableState:
    """
    Public state of the table.
    """

    recent_cards: list[Card] = field(default_factory=list)

    top_card: Optional[Card] = None

    required_suit: Optional[Suit] = None

    ace_effect_active: bool = False

    bank_size: int = 0

    played_pile_size: int = 0


@dataclass(slots=True)
class TurnState:
    """
    Information about the current turn.
    """

    is_your_turn: bool = False

    can_draw: bool = False

    can_pass: bool = False

    draw_count_if_draw: int = 0


@dataclass(slots=True)
class GameState:
    """
    Internal representation of the game state used by Master-i151.

    This object represents what the bot knows about the game.
    It is NOT the raw engine state.

    Hidden information must never be represented as known facts.
    """

    you: PlayerState = field(default_factory=PlayerState)

    opponent: PlayerState = field(default_factory=PlayerState)

    table: TableState = field(default_factory=TableState)

    turn: TurnState = field(default_factory=TurnState)

    # ------------------------------------------------------------------
    # Game-level information
    # ------------------------------------------------------------------

    target_score: int = 151

    round_number: int = 0

    round_active: bool = False

    # ------------------------------------------------------------------
    # Observation state
    # ------------------------------------------------------------------

    step_index: int = 0

    def is_game_over(self) -> bool:
        """
        Whether one of the players has reached the elimination threshold.
        """

        return (
            self.you.total_score >= self.target_score
            or self.opponent.total_score >= self.target_score
        )

    def is_you_eliminated(self) -> bool:
        return self.you.total_score >= self.target_score

    def is_opponent_eliminated(self) -> bool:
        return self.opponent.total_score >= self.target_score

    def current_hand_points_difference(self) -> int:
        """
        Positive value means our current hand contains more points.
        """

        return self.you.hand_points - self.opponent.hand_points

    def score_difference(self) -> int:
        """
        Positive value means our cumulative game score is higher.
        """

        return self.you.total_score - self.opponent.total_score