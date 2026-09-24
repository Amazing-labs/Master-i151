from __future__ import annotations

from dataclasses import dataclass, field

from .cards import Card, standard_deck
from .memory import ObservationMemory
from .state import GameState


@dataclass(slots=True)
class KnowledgeEngine:
    """
    Maintains the knowledge accumulated by the bot during a game.

    Responsibilities:
        - observe the current GameState;
        - remember cards that have been observed;
        - identify cards whose location is currently unknown;
        - identify cards that could potentially be in the opponent's hand.

    Non-responsibilities:
        - choosing an action;
        - evaluating the quality of an action;
        - implementing game rules;
        - predicting the exact opponent hand.

    Important:
        The bot only has partial information about the game.

        Unknown cards belong to the set:

            bank + opponent hand

        Therefore, an unknown card must NOT be considered an opponent card
        with certainty.
    """

    memory: ObservationMemory = field(
        default_factory=ObservationMemory
    )

    known_cards: set[Card] = field(default_factory=set)

    unknown_cards: set[Card] = field(default_factory=set)

    possible_opponent_cards: set[Card] = field(default_factory=set)

    deck: set[Card] = field(
        default_factory=standard_deck
    )

    def observe(self, state: GameState) -> None:
        """
        Update the knowledge engine from the current game state.

        The current state provides new observable information.
        That information is added to persistent memory and used to
        recompute the current knowledge.

        This method does not make strategic decisions.
        """

        self.memory.step_count += 1

        self._remember_observed_cards(state)

        self._recompute_knowledge(state)

    def reset(self) -> None:
        """
        Reset all knowledge.

        This should normally be called when starting a new game,
        because knowledge from a previous game must not leak into
        the next one.
        """

        self.memory.reset()

        self.known_cards.clear()
        self.unknown_cards.clear()
        self.possible_opponent_cards.clear()

    def _remember_observed_cards(self, state: GameState) -> None:
        """
        Store cards that are currently observable.

        We know:
            - cards in our hand;
            - cards publicly visible on the table;
            - cards previously observed and stored in memory.
        """

        self.memory.observe_cards(state.you.hand)
        self.memory.observe_cards(state.table.recent_cards)

    def _recompute_knowledge(self, state: GameState) -> None:
        """
        Recompute the current knowledge from the accumulated observations.
        """

        self.known_cards.clear()
        self.unknown_cards.clear()
        self.possible_opponent_cards.clear()

        # --------------------------------------------------------------
        # 1. Cards currently in our hand are known.
        # --------------------------------------------------------------

        self.known_cards.update(state.you.hand)

        # --------------------------------------------------------------
        # 2. Publicly visible cards are known.
        # --------------------------------------------------------------

        self.known_cards.update(state.table.recent_cards)

        # --------------------------------------------------------------
        # 3. Previously observed cards remain known.
        # --------------------------------------------------------------

        self.known_cards.update(self.memory.observed_cards)

        # --------------------------------------------------------------
        # 4. Every card that we have not identified belongs to the
        #    unknown pool.
        #
        #    According to the documented information model:
        #
        #        unknown cards = bank + opponent hand
        #
        #    We therefore cannot determine their exact location.
        # --------------------------------------------------------------

        self.unknown_cards.update(
            self.deck - self.known_cards
        )

        # --------------------------------------------------------------
        # 5. Every unknown card is a possible opponent card.
        #
        #    This does NOT mean that the card is actually in the
        #    opponent's hand.
        # --------------------------------------------------------------

        self.possible_opponent_cards.update(
            self.unknown_cards
        )

    def knows(self, card: Card) -> bool:
        """
        Return True if the bot has observed this card.
        """

        return card in self.known_cards

    def is_unknown(self, card: Card) -> bool:
        """
        Return True if the card's current location is unknown.
        """

        return card in self.unknown_cards

    def may_be_in_opponent_hand(self, card: Card) -> bool:
        """
        Return True if the card could currently be in the opponent's hand.

        This is a possibility, not a certainty.
        """

        return card in self.possible_opponent_cards

    def known_card_count(self) -> int:
        """
        Number of distinct cards currently known.
        """

        return len(self.known_cards)

    def unknown_card_count(self) -> int:
        """
        Number of cards whose current location is unknown.
        """

        return len(self.unknown_cards)

    def possible_opponent_card_count(self) -> int:
        """
        Number of cards that could potentially be in the opponent's hand.
        """

        return len(self.possible_opponent_cards)

    def get_known_cards(self) -> frozenset[Card]:
        """
        Return an immutable snapshot of the currently known cards.
        """

        return frozenset(self.known_cards)

    def get_unknown_cards(self) -> frozenset[Card]:
        """
        Return an immutable snapshot of the currently unknown cards.
        """

        return frozenset(self.unknown_cards)

    def get_possible_opponent_cards(self) -> frozenset[Card]:
        """
        Return an immutable snapshot of cards that may be in the
        opponent's hand.
        """

        return frozenset(self.possible_opponent_cards)