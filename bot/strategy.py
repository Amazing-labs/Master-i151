"""Strategy engine: chooses among the options the engine declared legal.

It only sees domain types (`GameState`, `cards.Card`, `KnowledgeEngine`) and
answers with an index into the options it was given, so it can never build an
illegal action. Ties keep the first option, in engine order.

Current behaviour is bot V2.3 (see docs/experiments.md): a play is scored by
the best sequence it opens within the same turn (same-rank chaining, Queen
extra turn in a duel).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from cards import Card, Rank, Suit
from game_state import GameState
from knowledge import KnowledgeEngine
from rules import can_play_with_required_suit, continues_by_chaining, queen_grants_extra_turn
from weights import DEFAULT_WEIGHTS, Weights


@dataclass(frozen=True, slots=True)
class Options:
    """Legal options of the current step, in engine order."""

    suits: tuple[Suit | None, ...] = ()
    plays: tuple[tuple[Card, ...], ...] = ()
    can_pass: bool = False


class DecisionKind(Enum):
    CHOOSE_SUIT = "choose_suit"
    PLAY = "play"
    PASS = "pass"
    DEFAULT = "default"  # first legal action (usually a draw)


@dataclass(frozen=True, slots=True)
class Decision:
    kind: DecisionKind
    index: int = 0


class StrategyEngine:
    def __init__(self, weights: Weights = DEFAULT_WEIGHTS) -> None:
        self.weights = weights

    def decide(self, state: GameState, knowledge: KnowledgeEngine, options: Options) -> Decision:
        # `knowledge` is not used by the V2.3 heuristics yet; it is wired so
        # that future heuristics can be added and benchmarked one at a time.
        del knowledge

        if options.suits:
            return Decision(DecisionKind.CHOOSE_SUIT, _argmax(
                self._suit_score(state, suit) for suit in options.suits
            ))
        if options.plays:
            return Decision(DecisionKind.PLAY, _argmax(
                self._play_score(state, cards) for cards in options.plays
            ))
        if options.can_pass:
            return Decision(DecisionKind.PASS)
        return Decision(DecisionKind.DEFAULT)

    # ------------------------------------------------------------------
    # Plays
    # ------------------------------------------------------------------

    def _play_score(self, state: GameState, cards: tuple[Card, ...]) -> float:
        """A single card is worth the best sequence it opens within the turn."""
        if len(cards) != 1:
            return self._sequence_score(state, cards)
        return max(
            self._sequence_score(state, sequence)
            for sequence in turn_sequences(state, cards[0])
        )

    def _sequence_score(self, state: GameState, cards: Sequence[Card]) -> float:
        w = self.weights
        if not cards:
            return float("-inf")

        hand_size = state.you.hand_size
        duel = state.player_count == 2

        if duel and len(cards) == hand_size and cards[-1].rank is Rank.QUEEN:
            return w.finishes_on_queen

        opponent_count = state.opponent.hand_size
        played_count = len(cards)
        remaining_count = hand_size - played_count
        dumped_points = sum(card.points for card in cards)

        score = played_count * w.per_card_played
        score += dumped_points * w.per_point_dumped
        score += remaining_count * w.per_card_remaining

        if remaining_count == 0:
            score += w.empties_hand

        if opponent_count <= w.short_opponent_cards:
            score += played_count * w.race_per_card_played
            score += remaining_count * w.race_per_card_remaining

        if hand_size <= w.short_hand_cards:
            score += played_count * w.short_hand_per_card_played

        if cards[-1].rank is Rank.QUEEN and duel and remaining_count > 0:
            if opponent_count <= 2:
                score += w.queen_skip_opponent_le_2
            elif opponent_count <= 4:
                score += w.queen_skip_opponent_le_4
            else:
                score += w.queen_skip_otherwise

        for card in cards:
            score += self._card_context(state, card, remaining_count)

        if remaining_count == 1 and duel:
            left = _remaining_hand(state.you.hand, cards)
            if len(left) == 1 and left[0].rank is Rank.QUEEN:
                score += w.single_queen_left

        return score

    def _card_context(self, state: GameState, card: Card, remaining_count: int) -> float:
        w = self.weights
        opponent_count = state.opponent.hand_size
        hand_size = state.you.hand_size
        bonus = 0.0

        if card.rank is Rank.EIGHT:
            if opponent_count <= w.short_opponent_cards or remaining_count <= w.eight_late_remaining_cards:
                bonus += w.eight_late
            elif hand_size >= w.eight_big_hand_cards:
                bonus += w.eight_big_hand
            elif hand_size >= w.eight_medium_hand_cards:
                bonus += w.eight_medium_hand
            else:
                bonus += w.eight_small_hand

        if card.rank is Rank.ACE:
            if state.table.ace_effect_active:
                bonus += w.ace_effect_already_active
            elif _ace_is_tactical(state):
                bonus += w.ace_tactical
            elif opponent_count <= w.short_opponent_cards:
                bonus += w.ace_short_opponent

        return bonus

    # ------------------------------------------------------------------
    # Suit choice
    # ------------------------------------------------------------------

    def _suit_score(self, state: GameState, suit: Suit | None) -> float:
        w = self.weights
        if suit is None:
            return float("-inf")

        hand_counts = Counter(card.suit for card in state.you.hand)
        table_counts = Counter(card.suit for card in _seen_table_cards(state))

        score = hand_counts[suit] * w.suit_per_card_in_hand
        score += table_counts[suit] * w.suit_per_card_on_table

        if hand_counts[suit] + table_counts[suit] >= w.suit_nearly_exhausted_cards:
            score += w.suit_nearly_exhausted

        if hand_counts[suit] == 0:
            score += w.suit_absent_from_hand

        return score


def turn_sequences(state: GameState, first: Card) -> list[tuple[Card, ...]]:
    """Every card sequence `first` can open within the current turn.

    Continuations follow rules.continues_by_chaining and
    rules.queen_grants_extra_turn. An eight ends the sequence (suit choice;
    chaining eights is not explored).
    """
    sequences: list[tuple[Card, ...]] = []
    active_players = state.active_player_count

    def explore(hand: list[Card], top: Card | None, played: list[Card]) -> None:
        sequences.append(tuple(played))
        card = played[-1]

        if not hand or card.rank is Rank.EIGHT:
            return

        if continues_by_chaining(card, top, hand):
            nexts = [c for c in hand if c.rank is card.rank]
        elif queen_grants_extra_turn(card, active_players):
            nexts = [c for c in hand if can_play_with_required_suit(c, card, None)]
        else:
            return

        for nxt in nexts:
            rest = list(hand)
            rest.remove(nxt)
            explore(rest, card, played + [nxt])

    hand = list(state.you.hand)
    if first in hand:
        hand.remove(first)
    explore(hand, state.table.top_card, [first])
    return sequences


def _argmax(scores) -> int:
    """Index of the first maximum (same tie-break as `max`)."""
    best_index, best_score = 0, None
    for index, score in enumerate(scores):
        if best_score is None or score > best_score:
            best_index, best_score = index, score
    return best_index


def _remaining_hand(hand: Sequence[Card], played: Sequence[Card]) -> list[Card]:
    left = list(hand)
    for card in played:
        if card in left:
            left.remove(card)
    return left


def _ace_is_tactical(state: GameState) -> bool:
    """Playing an ace is tactical when we cannot follow the current suit."""
    if state.table.ace_effect_active:
        return False

    hand_counts = Counter(card.suit for card in state.you.hand)
    required_suit = state.table.required_suit
    if required_suit is not None:
        return hand_counts[required_suit] == 0

    top_card = state.table.top_card
    if top_card is None:
        return False
    if top_card.rank is Rank.ACE:
        return True
    return hand_counts[top_card.suit] == 0


def _seen_table_cards(state: GameState) -> list[Card]:
    seen = list(state.table.recent_cards)
    for card in state.table.last_play_cards:
        if card not in seen:
            seen.append(card)
    return seen
