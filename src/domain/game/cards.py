from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Suit(str, Enum):
    CLUBS = "C"
    DIAMONDS = "D"
    HEARTS = "H"
    SPADES = "S"


class Rank(str, Enum):
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "T"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


CARD_POINTS: dict[Rank, int] = {
    Rank.SEVEN: 7,
    Rank.EIGHT: 32,
    Rank.NINE: 9,
    Rank.TEN: 10,
    Rank.JACK: 2,
    Rank.QUEEN: 3,
    Rank.KING: 4,
    Rank.ACE: 11,
}


@dataclass(frozen=True, slots=True)
class Card:
    """
    Immutable representation of a game card.

    Example:
        Card(Rank.EIGHT, Suit.HEARTS)
        -> 8H
    """

    rank: Rank
    suit: Suit

    @property
    def points(self) -> int:
        return CARD_POINTS[self.rank]

    @property
    def is_eight(self) -> bool:
        return self.rank is Rank.EIGHT

    @property
    def is_ace(self) -> bool:
        return self.rank is Rank.ACE
    
    def standard_deck() -> set[Card]:
    """
    Return the 32-card deck used by the documented game version.
    """

    return {
        Card(rank, suit)
        for rank in Rank
        for suit in Suit
    }

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"