from __future__ import annotations

from i151_engine.models.card import standard_deck as engine_deck

from arena_adapter import to_card
from cards import standard_deck


def test_deck_has_32_distinct_cards():
    assert len(standard_deck()) == 32


def test_every_engine_card_maps_to_a_domain_card_with_the_same_points():
    mapped = {to_card(card) for card in engine_deck()}
    assert mapped == standard_deck()
    for card in engine_deck():
        assert to_card(card).points == card.points
