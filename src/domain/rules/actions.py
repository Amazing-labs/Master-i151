"""
Kanté — Rules & Actions Engine
================================

Ce module répond à UNE question : « quelles actions, parmi celles fournies
par le moteur (legal_actions), appartiennent à telle catégorie ? »

Principe (voir guide §6.4) :
    legal_actions = vérité du moteur.
    Ce module ne réinvente jamais le moteur i151 : il se contente
    d'analyser et de classer ce que le moteur a déjà déclaré légal.

Ce module ne doit JAMAIS :
    - choisir la meilleure action (❌ max(actions, ...))       -> strategy/
    - coder une heuristique (❌ if opponent.hand_size <= 2)     -> strategy/
"""

from __future__ import annotations

from i151_engine.models.action import Action, ActionType

__all__ = [
    "get_play_actions",
    "get_single_play_actions",
    "get_multi_play_actions",
    "get_draw_actions",
    "get_pass_actions",
    "get_suit_choices",
    "group_by_type",
    "count_by_type",
    "distinct_playable_cards",
]


def get_single_play_actions(legal_actions: list[Action]) -> list[Action]:
    """Actions PLAY_CARD (une seule carte posée)."""
    return [a for a in legal_actions if a.type == ActionType.PLAY_CARD]


def get_multi_play_actions(legal_actions: list[Action]) -> list[Action]:
    """Actions PLAY_MULTIPLE_CARDS (plusieurs cartes posées d'un coup)."""
    return [a for a in legal_actions if a.type == ActionType.PLAY_MULTIPLE_CARDS]


def get_play_actions(legal_actions: list[Action]) -> list[Action]:
    """Toute action qui pose au moins une carte (simple ou multiple)."""
    return [
        a
        for a in legal_actions
        if a.type in (ActionType.PLAY_CARD, ActionType.PLAY_MULTIPLE_CARDS)
    ]


def get_draw_actions(legal_actions: list[Action]) -> list[Action]:
    """Actions DRAW_CARD (piocher)."""
    return [a for a in legal_actions if a.type == ActionType.DRAW_CARD]


def get_pass_actions(legal_actions: list[Action]) -> list[Action]:
    """Actions PASS_TURN (passer)."""
    return [a for a in legal_actions if a.type == ActionType.PASS_TURN]


def get_suit_choices(legal_actions: list[Action]) -> list[Action]:
    """Actions CHOOSE_SUIT (choisir la couleur après un 8)."""
    return [a for a in legal_actions if a.type == ActionType.CHOOSE_SUIT]


def group_by_type(legal_actions: list[Action]) -> dict[ActionType, list[Action]]:
    """Regroupe les actions légales par ActionType.

    Utile pour Maiga (strategy/) qui veut itérer catégorie par catégorie
    sans réécrire les filtres ci-dessus.
    """
    grouped: dict[ActionType, list[Action]] = {t: [] for t in ActionType}
    for action in legal_actions:
        grouped[action.type].append(action)
    return grouped


def count_by_type(legal_actions: list[Action]) -> dict[ActionType, int]:
    """Dénombre les actions légales par type (debug / logs / tests)."""
    return {t: len(actions) for t, actions in group_by_type(legal_actions).items()}


def distinct_playable_cards(legal_actions: list[Action]) -> tuple:
    """Cartes distinctes jouables en solo (PLAY_CARD), sans doublon.

    Ne dit RIEN sur ce qu'il faut jouer : c'est juste un inventaire,
    pratique pour Maiga ou pour les tests.
    """
    seen = {}
    for action in get_single_play_actions(legal_actions):
        if action.card is not None:
            seen[action.card.code] = action.card
    return tuple(seen.values())
