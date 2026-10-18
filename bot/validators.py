"""
Kanté — Rules & Actions Engine : validation
=============================================

Deux niveaux de validation, volontairement séparés :

1. validate_structure(action)
   -> l'action est-elle bien formée en elle-même (contrat de la dataclass
      Action) ? Ex : une CHOOSE_SUIT sans chosen_suit est invalide.

2. ensure_legal(action, legal_actions)
   -> l'action correspond-elle à une des actions que le moteur a
      réellement autorisées ce tour-ci ?

Ce module ne décide jamais quoi jouer (ça, c'est strategy/). Il sert de
garde-fou juste avant de renvoyer une action au SDK, pour ne jamais
planter un match sur une "action illégale" (voir §16, Étape 3 : le bot
doit pouvoir jouer une partie complète sans exception/timeout/action
illégale).
"""

from __future__ import annotations

from i151_engine.models.action import Action, ActionType

from rules import is_multiple_card_play, is_single_card_play, is_suit_choice_required

__all__ = [
    "ActionValidationError",
    "validate_structure",
    "is_action_legal",
    "ensure_legal",
    "find_matching_legal_action",
]


class ActionValidationError(ValueError):
    """Levée quand une action est mal formée ou ne fait pas partie de legal_actions."""


def validate_structure(action: Action) -> list[str]:
    """Vérifie que l'action respecte le contrat de la dataclass Action.

    Retourne la liste des problèmes trouvés (liste vide = action bien
    formée). Ne dit rien sur la légalité vis-à-vis du moteur : voir
    `ensure_legal` pour ça.
    """
    problems: list[str] = []

    if is_suit_choice_required(action) and action.chosen_suit is None:
        problems.append("CHOOSE_SUIT sans chosen_suit renseigné")

    if is_single_card_play(action) and action.card is None:
        problems.append("PLAY_CARD sans carte renseignée")

    if is_multiple_card_play(action) and not action.cards:
        problems.append("PLAY_MULTIPLE_CARDS sans cartes renseignées")

    if action.type == ActionType.DRAW_CARD and action.card is not None:
        problems.append("DRAW_CARD ne devrait pas porter de carte")

    if action.type == ActionType.PASS_TURN and (
        action.card is not None or action.cards
    ):
        problems.append("PASS_TURN ne devrait porter aucune carte")

    return problems


def find_matching_legal_action(
    action: Action, legal_actions: list[Action]
) -> Action | None:
    """Retrouve l'action équivalente dans legal_actions, s'il y en a une.

    Action est une dataclass frozen avec égalité par valeur : deux Action
    construites séparément mais avec les mêmes champs sont égales. Ce
    helper existe surtout pour donner un message d'erreur utile quand ce
    n'est PAS le cas.
    """
    for candidate in legal_actions:
        if candidate == action:
            return candidate
    return None


def is_action_legal(action: Action, legal_actions: list[Action]) -> bool:
    """True si `action` fait partie de `legal_actions` fourni par le moteur."""
    return find_matching_legal_action(action, legal_actions) is not None


def ensure_legal(action: Action, legal_actions: list[Action]) -> Action:
    """Garde-fou final avant de renvoyer une action au SDK.

    Lève ActionValidationError si l'action est mal formée OU absente de
    legal_actions, plutôt que de laisser le moteur i151 rejeter l'action
    (ou pire, planter le match). À appeler en tout dernier, juste avant
    le `return` de decide().
    """
    problems = validate_structure(action)
    if problems:
        raise ActionValidationError(
            f"Action mal formée ({', '.join(problems)}) : {action!r}"
        )

    if not is_action_legal(action, legal_actions):
        raise ActionValidationError(
            f"Action hors legal_actions : {action!r} n'est pas dans "
            f"la liste des {len(legal_actions)} action(s) autorisée(s)."
        )

    return action
