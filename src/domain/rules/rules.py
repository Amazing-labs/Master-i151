"""
Kanté — Rules & Actions Engine : règles encapsulées
=====================================================

Les règles "découvertes" à propos du jeu ou du SDK vivent ICI, et nulle
part ailleurs (pas dans strategy/, pas dans bot.py).

Chaque règle est taguée avec son niveau de confiance (voir guide §6.5,
"Ne pas supposer une règle non confirmée") :

    RULE       -> règle écrite noir sur blanc dans la spec du jeu / le SDK.
    FACT       -> observée de façon fiable et reproductible dans le moteur
                  (ex : lue dans le code source public du SDK/engine).
    HYPOTHESIS -> pattern observé en partie, pas encore confirmé à 100%.
    UNKNOWN    -> comportement pas encore vérifié : NE PAS s'appuyer dessus.

But : que Maiga (strategy/) puisse dire `if rules.is_x(action):` sans
jamais avoir à relire la doc du SDK ou à deviner un comportement.
"""

from __future__ import annotations

from enum import Enum

from i151_engine.models.action import Action, ActionType
from i151_engine.models.card import Rank

__all__ = [
    "Confidence",
    "RULES_REGISTRY",
    "is_multiple_card_play",
    "is_single_card_play",
    "is_suit_choice_required",
    "is_draw",
    "is_pass",
    "is_play_of_eight",
    "requires_no_payload",
]


class Confidence(Enum):
    RULE = "RULE"
    FACT = "FACT"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


# Registre des règles documentées : une ligne = une règle, sa source, et
# son niveau de confiance. Objectif : éviter que deux personnes de l'équipe
# redécouvrent (ou se contredisent sur) la même règle.
RULES_REGISTRY: dict[str, tuple[Confidence, str]] = {
    "eight_is_always_playable": (
        Confidence.FACT,
        "Card.can_play_on : un 8 peut toujours être posé, quelle que soit "
        "la carte du dessus (arena_sdk / i151_engine.models.card).",
    ),
    "choose_suit_needs_a_suit": (
        Confidence.RULE,
        "Une action CHOOSE_SUIT n'a de sens que si chosen_suit est fourni "
        "(contrat de la dataclass Action du SDK).",
    ),
    "multiple_card_play_currently_unused": (
        Confidence.FACT,
        "PLAY_MULTIPLE_CARDS existe dans ActionType et dans la dataclass "
        "Action, mais legal_actions() ne l'a JAMAIS produit sur 2000 parties "
        "aléatoires complètes simulées avec le moteur publié (i151_engine "
        "0.2.4, ~1M actions légales observées au total, voir "
        "tests/rules/test_engine_integration.py). Reclassé FACT (et non "
        "plus HYPOTHESIS) sur la base de cette mesure, mais ce n'est pas "
        "une RULE écrite dans le règlement : à reconfirmer si le moteur "
        "est mis à jour (nouvelle version PyPI).",
    ),
}


def is_single_card_play(action: Action) -> bool:
    """RULE — action qui pose exactement une carte."""
    return action.type == ActionType.PLAY_CARD


def is_multiple_card_play(action: Action) -> bool:
    """RULE — action qui pose plusieurs cartes d'un coup.

    Voir RULES_REGISTRY["multiple_card_play_currently_unused"] : ce type
    est valide dans le contrat du SDK même s'il est rarement/jamais vu
    en pratique pour l'instant.
    """
    return action.type == ActionType.PLAY_MULTIPLE_CARDS


def is_draw(action: Action) -> bool:
    """RULE — action de pioche."""
    return action.type == ActionType.DRAW_CARD


def is_pass(action: Action) -> bool:
    """RULE — action de passage."""
    return action.type == ActionType.PASS_TURN


def is_suit_choice_required(action: Action) -> bool:
    """RULE — cette action doit obligatoirement porter un chosen_suit.

    Ne prédit PAS si un choix de couleur arrivera au tour suivant (ça,
    c'est de la connaissance sur l'état du moteur, hors périmètre de ce
    module — voir §6.4). Ici on ne fait que dire : "pour CETTE action,
    le champ chosen_suit est obligatoire".
    """
    return action.type == ActionType.CHOOSE_SUIT


def is_play_of_eight(action: Action) -> bool:
    """FACT — l'action pose (au moins) un 8.

    Utile car un 8 a un statut spécial : toujours jouable, et déclenche
    un choix de couleur (RULES_REGISTRY["eight_is_always_playable"]).
    """
    if action.card is not None and action.card.rank == Rank.EIGHT:
        return True
    return any(c.rank == Rank.EIGHT for c in action.cards)


def requires_no_payload(action: Action) -> bool:
    """RULE — action "nue" : ni carte, ni chosen_suit (DRAW / PASS)."""
    return action.type in (ActionType.DRAW_CARD, ActionType.PASS_TURN)
