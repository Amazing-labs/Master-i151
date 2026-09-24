from __future__ import annotations

from dataclasses import dataclass, field

from .cards import Card, standard_deck
from .memory import ObservationMemory
from .state import GameState


@dataclass(slots=True)
class KnowledgeEngine:
    """
    Maintains the bot's accumulated knowledge.

    Responsibilities:
        - observe the game
        - remember public information
        - track known cards
        - compute possible unknown cards

    Non-responsibilities:
        - choosing actions
        - evaluating strategies
        - deciding whether an action is good
    """

    memory: ObservationMemory = field(
        default_factory=ObservationMemory
    )

    knowledge: KnowledgeState = field(
        default_factory=KnowledgeState
    )

    deck: set[Card] = field(
        default_factory=standard_deck
    )

    def observe(self, state: GameState) -> None:
        """
        Update persistent knowledge from the current GameState.
        """

        self.memory.step_count += 1

        self.memory.observe_cards(state.you.hand)
        self.memory.observe_cards(state.table.recent_cards)

        self.knowledge.update(
            state=state,
            memory=self.memory,
            full_deck=self.deck,
        )

    def reset(self) -> None:
        self.memory.reset()

        self.knowledge.known_cards.clear()
        self.knowledge.possible_opponent_cards.clear()
        self.knowledge.unknown_cards.clear()

    def known_card_count(self) -> int:
        return len(self.knowledge.known_cards)

    def unknown_card_count(self) -> int:
        return len(self.knowledge.unknown_cards)