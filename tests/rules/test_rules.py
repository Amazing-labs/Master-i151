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

import rules as R

CARD_8S = Card(rank=Rank.EIGHT, suit=Suit.SPADES)
CARD_9H = Card(rank=Rank.NINE, suit=Suit.HEARTS)
CARD_KD = Card(rank=Rank.KING, suit=Suit.DIAMONDS)


# ---------------------------------------------------------------------------
# Règles encapsulées (rules.py)
# ---------------------------------------------------------------------------


def test_is_suit_choice_required_action_necessitant_chosen_suit():
    assert R.is_suit_choice_required(Action.choose_suit(Suit.HEARTS)) is True
    assert R.is_suit_choice_required(Action.play_card(CARD_9H)) is False


def test_is_multiple_card_play():
    assert R.is_multiple_card_play(Action.play_multiple_cards([CARD_9H, CARD_KD])) is True
    assert R.is_multiple_card_play(Action.play_card(CARD_9H)) is False


def test_is_play_of_eight():
    assert R.is_play_of_eight(Action.play_card(CARD_8S)) is True
    assert R.is_play_of_eight(Action.play_card(CARD_9H)) is False
    assert R.is_play_of_eight(Action.play_multiple_cards([CARD_8S, CARD_9H])) is True


def test_requires_no_payload():
    assert R.requires_no_payload(Action.draw_card()) is True
    assert R.requires_no_payload(Action.pass_turn()) is True
    assert R.requires_no_payload(Action.play_card(CARD_9H)) is False
