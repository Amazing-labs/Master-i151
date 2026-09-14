"""Bot i151 — implémentez setup / decide / observe / teardown."""

from pathlib import Path

from arena_sdk import Action, PlayerView


def setup(submission_dir: Path) -> None:
    """Optionnel — charger un modèle une fois au début du match."""
    pass


def decide(view: PlayerView, legal_actions: list[Action], time_left_ms: int) -> Action:
    """Choisir une action légale (sinon → forfait)."""
    return legal_actions[0]


def observe(view: PlayerView) -> None:
    """Optionnel — appelé après chaque action (y compris adverses)."""
    pass


def teardown() -> None:
    """Optionnel — libérer la mémoire après le match."""
    pass
