from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from cards import Card, Suit, standard_deck
from game_state import GameState


@dataclass(slots=True)
class KnowledgeEngine:
    """
    Card knowledge accumulated by the bot during one round.

    Every card is in exactly one of four places:

        our hand        -> known (from the view)
        played pile     -> partly known (reconstructed from observations)
        bank            -> unknown
        opponent hand   -> unknown

    The engine shuffles the whole played pile back into the bank when the bank
    runs out (i151_engine.core.reducer._draw_with_refill), so a card seen on
    the table is NOT out of play for the rest of the round. The pile is
    therefore tracked position by position, and a position whose card was not
    observed stays unknown (None).

    Unknown cards belong to bank + opponent hand + unknown pile positions.
    An unknown card is never treated as an opponent card: only a uniform
    probability is exposed.

    Observations come from `decide` views and from `observe` views (sent after
    every opponent action), so normally no play is missed.
    """

    deck: frozenset[Card] = field(default_factory=lambda: frozenset(standard_deck()))

    round_number: int | None = None

    last_step_index: int = -1

    hand: frozenset[Card] = frozenset()

    pile: list[Card | None] = field(default_factory=list)

    opponent_hand_size: int = 0

    bank_size: int = 0

    unknown_cards: frozenset[Card] = frozenset()

    # Bank order once the pile has been shuffled back into it (front = next
    # draw). The engine appends the pile in play order after the few cards
    # left in the bank, so the order is known except those first cards.
    bank_order: list[Card | None] | None = None

    # Cards certainly in the opponent's hand: drawn from a known bank order.
    opponent_known: set[Card] = field(default_factory=set)

    def reset(self) -> None:
        """Forget everything (new match)."""
        self.round_number = None
        self.last_step_index = -1
        self.hand = frozenset()
        self.pile = []
        self.opponent_hand_size = 0
        self.bank_size = 0
        self.unknown_cards = frozenset()
        self.bank_order = None
        self.opponent_known = set()

    def observe(self, state: GameState) -> None:
        """Update the knowledge from one observable state. Makes no decision."""
        new_round = state.round_number != self.round_number
        new_match = state.step_index < self.last_step_index
        if new_round or new_match:
            self.reset()
            self.round_number = state.round_number
            fresh = True
        else:
            fresh = False

        previous_pile = self.pile
        previous_bank = self.bank_size
        previous_hand = self.hand
        hand_now = frozenset(state.you.hand)

        if not fresh:
            self._track_bank(state, previous_pile, previous_bank, previous_hand, hand_now)

        self.last_step_index = state.step_index
        self.hand = hand_now
        self.opponent_hand_size = state.opponent.hand_size
        self.bank_size = state.table.bank_size
        self._sync_pile(state.table.played_pile_size, state.table.recent_cards)

        self.opponent_known -= self.known_pile_cards()
        self.opponent_known -= self.hand
        if len(self.opponent_known) > self.opponent_hand_size:
            self.opponent_known = set()  # inconsistent (engine duplication bug)

        self.unknown_cards = (
            self.deck - self.hand - self.known_pile_cards()
            - self.known_bank_cards() - frozenset(self.opponent_known)
        )

    def _track_bank(self, state, previous_pile, previous_bank, previous_hand, hand_now) -> None:
        """Follow the bank order through refills and draws (one gap between
        observations holds at most our action, then one opponent action)."""
        played_by_us = [card for card in previous_hand if card not in hand_now]
        refilled = (
            state.table.played_pile_size < len(previous_pile)
            or state.table.bank_size > previous_bank
        )
        if refilled:
            self.bank_order = [None] * previous_bank + list(previous_pile) + played_by_us
            self.opponent_known = set()  # recomputed from the new order

        if self.bank_order is None:
            return
        consumed = len(self.bank_order) - state.table.bank_size
        if consumed < 0:
            self.bank_order = None
            return
        drawn = self.bank_order[:consumed]
        self.bank_order = self.bank_order[consumed:]

        # Our action comes first in the gap, so our draws are the first cards.
        ours = len(hand_now) - (len(previous_hand) - len(played_by_us))
        ours = max(0, min(ours, consumed))
        self.opponent_known.update(card for card in drawn[ours:] if card is not None)

    def _sync_pile(self, size: int, recent: list[Card]) -> None:
        """Align the tracked pile with its observed size and visible tail."""
        pile = self.pile
        candidate: list[Card | None] | None = None

        if size >= len(pile):
            added = size - len(pile)
            if added <= len(recent):
                candidate = pile + list(recent[len(recent) - added:]) if added else list(pile)
            else:
                candidate = pile + [None] * (added - len(recent)) + list(recent)

        # A smaller pile means it was shuffled back into the bank; a tail that
        # disagrees with the visible cards means we lost track. In both cases
        # keep only what is visible now.
        if candidate is None or (recent and candidate[-len(recent):] != list(recent)):
            candidate = [None] * (size - len(recent)) + list(recent)

        self.pile = candidate

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def known_pile_cards(self) -> frozenset[Card]:
        """Cards certainly in the played pile right now."""
        return frozenset(card for card in self.pile if card is not None)

    def known_bank_cards(self) -> frozenset[Card]:
        """Cards certainly in the bank (known order after a refill)."""
        if self.bank_order is None:
            return frozenset()
        return frozenset(card for card in self.bank_order if card is not None)

    def unknown_pile_count(self) -> int:
        """Pile positions whose card was never observed."""
        return sum(1 for card in self.pile if card is None)

    def knows(self, card: Card) -> bool:
        """True if the card's location is certain (our hand or the pile)."""
        return card not in self.unknown_cards

    def is_unknown(self, card: Card) -> bool:
        return card in self.unknown_cards

    def may_be_in_opponent_hand(self, card: Card) -> bool:
        """A possibility, not a certainty."""
        return card in self.opponent_known or (
            self.opponent_hand_size > len(self.opponent_known) and card in self.unknown_cards
        )

    def opponent_probability(self, card: Card) -> float:
        """Probability that `card` is in the opponent's hand, assuming every
        unknown card is equally likely to be in any unknown location."""
        if card in self.opponent_known:
            return 1.0
        if card not in self.unknown_cards or not self.unknown_cards:
            return 0.0
        return (self.opponent_hand_size - len(self.opponent_known)) / len(self.unknown_cards)

    def unknown_count_by_suit(self) -> Counter[Suit]:
        return Counter(card.suit for card in self.unknown_cards)

    def known_card_count(self) -> int:
        return len(self.deck) - len(self.unknown_cards)

    def unknown_card_count(self) -> int:
        return len(self.unknown_cards)
