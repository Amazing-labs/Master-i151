"""
Tests d'intégration Kanté contre le vrai moteur (i151_engine).

Objectif (voir infographie §2, colonne Kanté) :
    - "Tests des comportements moteur"
    - "Vérification de la légalité des actions"
    - "Analyse des zones inconnues"

Contrairement à test_rules_engine.py (qui construit des Action à la main),
ce fichier fait tourner de VRAIES parties aléatoires à travers le moteur
publié, et vérifie que nos modules (actions.py / rules.py / validators.py)
se comportent correctement face à des `legal_actions` réelles — pas
seulement des cas fabriqués à la main.

Ces tests sont volontairement un peu lents (parties complètes) : à lancer
séparément des tests unitaires rapides si besoin (`pytest -m integration`).
"""

from __future__ import annotations

import random
from dataclasses import replace

import pytest
from i151_engine.core.legal_actions import legal_actions as engine_legal_actions
from i151_engine.core.reducer import apply_action
from i151_engine.game.round import create_match
from i151_engine.models.action import ActionType
from i151_engine.models.enums import MatchStatus

import actions as A
import validators as V

pytestmark = pytest.mark.integration

N_GAMES = 60
MAX_STEPS = 3000


def _play_random_game(seed: int):
    """Joue une partie aléatoire complète et retourne chaque `legal_actions`
    observé, tour par tour (générateur)."""
    match = create_match(("A", "B"), seed=seed)
    rng = random.Random(seed)
    steps = 0
    while match.status == MatchStatus.IN_PROGRESS and steps < MAX_STEPS:
        round_state = match.current_round
        if round_state is None:
            return
        legal = engine_legal_actions(round_state)
        if not legal:
            return
        yield legal
        chosen = rng.choice(legal)
        match = replace(match, current_round=apply_action(round_state, chosen))
        steps += 1


def test_classification_partitionne_toutes_les_legal_actions_reelles():
    """Chaque action légale réelle doit tomber dans exactement une des
    catégories connues (play simple, play multiple, draw, pass, suit)."""
    for seed in range(N_GAMES):
        for legal in _play_random_game(seed):
            categorized = (
                len(A.get_single_play_actions(legal))
                + len(A.get_multi_play_actions(legal))
                + len(A.get_draw_actions(legal))
                + len(A.get_pass_actions(legal))
                + len(A.get_suit_choices(legal))
            )
            assert categorized == len(legal), (
                "Une action légale réelle n'a été classée dans aucune "
                "catégorie connue de actions.py — ActionType inattendu."
            )


def test_toute_action_legale_reelle_passe_la_validation_structurelle():
    """Une action produite par le VRAI moteur ne doit jamais être signalée
    comme mal formée par validators.validate_structure — sinon notre
    compréhension du contrat Action est fausse quelque part."""
    for seed in range(N_GAMES):
        for legal in _play_random_game(seed):
            for action in legal:
                problems = V.validate_structure(action)
                assert problems == [], (
                    f"validate_structure rejette une action réellement "
                    f"légale : {action!r} -> {problems}"
                )


def test_ensure_legal_accepte_chaque_action_reellement_legale():
    for seed in range(min(N_GAMES, 20)):
        for legal in _play_random_game(seed):
            for action in legal:
                # Ne doit jamais lever : c'est une action réellement légale.
                V.ensure_legal(action, legal)


def test_zone_inconnue_play_multiple_cards_jamais_observe():
    """Analyse de zone inconnue (§ infographie, Kanté) : PLAY_MULTIPLE_CARDS
    est un ActionType valide dans le SDK mais n'a, à date, jamais été vu
    produit par legal_actions() du moteur publié.

    Si ce test échoue un jour, c'est une bonne nouvelle : ça veut dire que
    le moteur a évolué et qu'il faut mettre à jour la confiance de la règle
    dans rules.RULES_REGISTRY (actuellement FACT, pas RULE).
    """
    seen_multiple = False
    for seed in range(N_GAMES):
        for legal in _play_random_game(seed):
            if any(a.type == ActionType.PLAY_MULTIPLE_CARDS for a in legal):
                seen_multiple = True
    assert seen_multiple is False
