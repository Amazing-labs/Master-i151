from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol

from .scenarios import Scenario


@dataclass(frozen=True, slots=True)
class SimulationConfig:
	bot: str
	opponent: str
	games: int
	seed_start: int = 0
	bot_version: str = "unversioned"
	scenario_name: str | None = None
	conditions: Mapping[str, Any] = field(default_factory=dict)

	def __post_init__(self) -> None:
		if not self.bot.strip() or not self.opponent.strip():
			raise ValueError("Bot and opponent names must not be empty")
		if self.games < 1:
			raise ValueError("games must be at least one")


@dataclass(frozen=True, slots=True)
class MatchRecord:
	seed: int
	winner: str | None = None
	winner_known: bool = False
	scores: Mapping[str, int] = field(default_factory=dict)
	rounds_won: Mapping[str, int] = field(default_factory=dict)
	turns: int | None = None
	decision_times_ms: tuple[float, ...] = ()
	metadata: Mapping[str, Any] = field(default_factory=dict)


class MatchExecutor(Protocol):
	def __call__(self, seed: int, scenario: Scenario | None) -> Any: ...


@dataclass(frozen=True, slots=True)
class SimulationRun:
	config: SimulationConfig
	results: tuple[MatchRecord, ...]

	def to_dict(self) -> dict[str, Any]:
		return {
			"config": asdict(self.config),
			"results": [asdict(result) for result in self.results],
		}

	def to_json(self) -> str:
		return json.dumps(self.to_dict(), sort_keys=True, default=str)


def _mapping_value(value: Any) -> Mapping[str, Any]:
	return value if isinstance(value, Mapping) else {}


def _sequence_value(value: Any) -> tuple[Any, ...]:
	if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
		return tuple(value)
	return ()


def _record_from_result(seed: int, result: Any) -> MatchRecord:
	if isinstance(result, MatchRecord):
		if result.seed != seed:
			raise ValueError(f"Executor returned seed {result.seed}; expected {seed}")
		return result
	if not isinstance(result, Mapping):
		raise TypeError("Match executor must return MatchRecord or a mapping")

	returned_seed = result.get("seed", seed)
	if returned_seed != seed:
		raise ValueError(f"Executor returned seed {returned_seed}; expected {seed}")
	times = result.get("decision_times_ms", result.get("decision_times", ()))
	turns = result.get("turns", result.get("total_turns"))
	return MatchRecord(
		seed=seed,
		winner=result.get("winner", result.get("winner_name")),
		winner_known="winner" in result or "winner_name" in result,
		scores=_mapping_value(result.get("scores", result.get("final_scores", {}))),
		rounds_won=_mapping_value(result.get("rounds_won", result.get("round_wins", {}))),
		turns=turns if isinstance(turns, int) and not isinstance(turns, bool) else None,
		decision_times_ms=tuple(
			float(value)
			for value in _sequence_value(times)
			if isinstance(value, (int, float)) and not isinstance(value, bool)
		),
		metadata=_mapping_value(result.get("metadata", {})),
	)


def run_simulation(
	executor: MatchExecutor | Callable[[int, Scenario | None], Any],
	config: SimulationConfig,
	*,
	scenario: Scenario | None = None,
) -> SimulationRun:
	"""Exécute la même configuration sur une plage de seeds reproductible.

	L'exécuteur prend en charge le démarrage du SDK/moteur, l'appel des bots, la
	collecte des replays et l'analyse des résultats. Les exceptions sont propagées
	avec leurs détails d'origine.
	"""

	if scenario is not None and config.scenario_name not in (None, scenario.name):
		raise ValueError("Scenario name does not match the simulation configuration")

	results = tuple(
		_record_from_result(seed, executor(seed, scenario))
		for seed in range(config.seed_start, config.seed_start + config.games)
	)
	return SimulationRun(config=config, results=results)
