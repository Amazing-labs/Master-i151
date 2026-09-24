from __future__ import annotations

from dataclasses import dataclass, field

from .cards import Card


@dataclass(slots=True)
class ObservationMemory:
    """
    Persistent memory across decide() calls.

    This memory contains observations made by the bot.
    It must not pretend to know hidden engine state.
    """

    observed_cards: list[Card] = field(default_factory=list)

    observed_card_set: set[Card] = field(default_factory=set)

    step_count: int = 0

    def observe_cards(self, cards: list[Card]) -> None:
        """
        Register cards observed by the bot.

        Duplicates are ignored.
        """

        for card in cards:
            if card not in self.observed_card_set:
                self.observed_card_set.add(card)
                self.observed_cards.append(card)

    def has_seen(self, card: Card) -> bool:
        return card in self.observed_card_set

    def reset(self) -> None:
        self.observed_cards.clear()
        self.observed_card_set.clear()
        self.step_count = 0