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
from src.domain.rules import validators as V

CARD_8S = Card(rank=Rank.EIGHT, suit=Suit.SPADES)
CARD_9H = Card(rank=Rank.NINE, suit=Suit.HEARTS)
CARD_KD = Card(rank=Rank.KING, suit=Suit.DIAMONDS)


# ---------------------------------------------------------------------------
# Validation (validators.py)
# ---------------------------------------------------------------------------


def test_validate_structure_action_bien_formee():
    assert V.validate_structure(Action.play_card(CARD_9H)) == []
    assert V.validate_structure(Action.choose_suit(Suit.CLUBS)) == []


def test_validate_structure_choose_suit_sans_suit_cas_limite():
    malformed = Action(type=ActionType.CHOOSE_SUIT)  # chosen_suit manquant
    problems = V.validate_structure(malformed)
    assert "CHOOSE_SUIT sans chosen_suit renseigné" in problems


def test_validate_structure_play_card_sans_carte_cas_limite():
    malformed = Action(type=ActionType.PLAY_CARD)  # card manquante
    problems = V.validate_structure(malformed)
    assert "PLAY_CARD sans carte renseignée" in problems


def test_is_action_legal_true_et_false():
    legal = [Action.play_card(CARD_9H), Action.draw_card()]
    assert V.is_action_legal(Action.play_card(CARD_9H), legal) is True
    assert V.is_action_legal(Action.play_card(CARD_KD), legal) is False


def test_ensure_legal_leve_si_action_hors_legal_actions_cas_limite():
    legal = [Action.draw_card()]
    with pytest.raises(V.ActionValidationError):
        V.ensure_legal(Action.pass_turn(), legal)


def test_ensure_legal_leve_si_action_mal_formee_cas_limite():
    legal = [Action(type=ActionType.CHOOSE_SUIT)]
    with pytest.raises(V.ActionValidationError):
        V.ensure_legal(Action(type=ActionType.CHOOSE_SUIT), legal)


def test_ensure_legal_ok_retourne_action():
    legal = [Action.draw_card()]
    assert V.ensure_legal(Action.draw_card(), legal) == Action.draw_card()


def test_legal_actions_vide_cas_limite():
    # Cas limite : aucune action légale fournie -> aucun helper ne doit planter.
    assert A.get_play_actions([]) == []
    assert A.get_draw_actions([]) == []
    assert A.count_by_type([])[ActionType.PLAY_CARD] == 0
    assert V.is_action_legal(Action.draw_card(), []) is False
