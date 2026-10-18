"""The domain playability rules must match the engine on every case."""

from __future__ import annotations

from i151_engine.models.card import Card as EngineCard
from i151_engine.models.card import Rank as EngineRank
from i151_engine.models.card import Suit as EngineSuit

from arena_adapter import to_card, to_suit
from rules import can_play_on, can_play_with_required_suit

ENGINE_DECK = [EngineCard(rank=rank, suit=suit) for suit in EngineSuit for rank in EngineRank]


def test_can_play_on_matches_engine_for_every_pair():
    for card in ENGINE_DECK:
        for other in ENGINE_DECK:
            assert can_play_on(to_card(card), to_card(other)) == card.can_play_on(other), (card, other)


def test_can_play_with_required_suit_matches_engine_everywhere():
    for card in ENGINE_DECK:
        for top in [None, *ENGINE_DECK]:
            for required in [None, *EngineSuit]:
                expected = card.can_play_on_with_required_suit(top, required)
                actual = can_play_with_required_suit(
                    to_card(card),
                    to_card(top) if top is not None else None,
                    to_suit(required),
                )
                assert actual == expected, (card, top, required)
