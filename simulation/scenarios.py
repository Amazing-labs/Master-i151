from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Scenario:
	"""Données nommées et sérialisables d'un scénario, gérées par l'adaptateur.

	Le contenu est volontairement opaque ici : ce paquet ne crée pas d'état de jeu
	et n'encode pas les règles. L'adaptateur peut ainsi utiliser le format de
	fixture que le moteur fournira.
	"""

	name: str
	payload: Mapping[str, Any] = field(default_factory=dict)
	description: str = ""
	tags: tuple[str, ...] = ()

	def __post_init__(self) -> None:
		if not self.name.strip():
			raise ValueError("Scenario name must not be empty")

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)
