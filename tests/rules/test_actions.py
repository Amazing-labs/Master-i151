"""
Tests attendus pour la mission Kanté (guide §6.6) :

    - Chaque type d'Action
    - Actions avec carte
    - Actions multiples
    - Actions nécessitant chosen_suit
    - Pioche normale
    - Pioche sous effet As
    - Passage
    - Choix de couleur
    - Cas limites
"""

from __future__ import annotations

import pytest
from i151_engine.models.action import Action, ActionType
from i151_engine.models.card import Card, Rank, Suit

from src.domain.rules import actions as A

CARD_8S = Card(rank=Rank.EIGHT, suit=Suit.SPADES)
CARD_9H = Card(rank=Rank.NINE, suit=Suit.HEARTS)
CARD_KD = Card(rank=Rank.KING, suit=Suit.DIAMONDS)


# ---------------------------------------------------------------------------
# Chaque type d'Action / classification (actions.py)
# ---------------------------------------------------------------------------


def test_get_single_play_actions():
    legal = [Action.play_card(CARD_9H), Action.draw_card()]
    result = A.get_single_play_actions(legal)
    assert result == [Action.play_card(CARD_9H)]


def test_get_multi_play_actions_actions_multiples():
    multi = Action.play_multiple_cards([CARD_9H, CARD_KD])
    legal = [Action.play_card(CARD_9H), multi]
    result = A.get_multi_play_actions(legal)
    assert result == [multi]


def test_get_play_actions_regroupe_simple_et_multiple():
    single = Action.play_card(CARD_9H)
    multi = Action.play_multiple_cards([CARD_9H, CARD_KD])
    legal = [single, multi, Action.draw_card()]
    result = A.get_play_actions(legal)
    assert set(result) == {single, multi}


def test_get_draw_actions_pioche_normale():
    legal = [Action.draw_card(), Action.pass_turn()]
    assert A.get_draw_actions(legal) == [Action.draw_card()]


def test_get_draw_actions_sous_effet_as():
    # Sous effet As, le moteur multiplie draw_count_if_draw, mais l'Action
    # elle-même reste un simple DRAW_CARD : la classification ne doit pas
    # changer de comportement (voir §6.4 : on ne réinvente pas le moteur).
    legal = [Action.draw_card()]
    result = A.get_draw_actions(legal)
    assert result == [Action.draw_card()]
    assert result[0].type == ActionType.DRAW_CARD


def test_get_pass_actions_passage():
    legal = [Action.pass_turn(), Action.draw_card()]
    assert A.get_pass_actions(legal) == [Action.pass_turn()]


def test_get_suit_choices_choix_de_couleur():
    legal = [Action.choose_suit(s) for s in Suit]
    result = A.get_suit_choices(legal)
    assert len(result) == 4
    assert all(a.type == ActionType.CHOOSE_SUIT for a in result)


def test_group_and_count_by_type():
    legal = [Action.play_card(CARD_9H), Action.draw_card(), Action.pass_turn()]
    grouped = A.group_by_type(legal)
    counts = A.count_by_type(legal)
    assert grouped[ActionType.PLAY_CARD] == [Action.play_card(CARD_9H)]
    assert counts[ActionType.PLAY_CARD] == 1
    assert counts[ActionType.CHOOSE_SUIT] == 0


def test_distinct_playable_cards_sans_doublon():
    legal = [Action.play_card(CARD_9H), Action.play_card(CARD_9H), Action.play_card(CARD_KD)]
    result = A.distinct_playable_cards(legal)
    assert set(c.code for c in result) == {CARD_9H.code, CARD_KD.code}
