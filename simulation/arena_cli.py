from __future__ import annotations

import json
from dataclasses import dataclass
from subprocess import run as run_process

from .runner import MatchRecord
from .scenarios import Scenario


_RESERVED_OPTIONS = {
	"--vs",
	"--seed",
	"--games",
	"--format",
	"--json",
	"--replay-out",
}


@dataclass(frozen=True, slots=True)
class ArenaCliExecutor:
	"""Exécute une partie avec seed via l'interface en ligne de commande Arena."""

	bot: str
	opponent: str = "random"
	executable: str = "arena"
	timeout_seconds: float = 300.0
	extra_options: tuple[str, ...] = ()

	def __post_init__(self) -> None:
		if not self.bot.strip() or not self.opponent.strip():
			raise ValueError("Bot and opponent identifiers must not be empty")
		if self.bot == self.opponent:
			raise ValueError("Bot and opponent identifiers must be distinct")
		if self.timeout_seconds <= 0:
			raise ValueError("timeout_seconds must be positive")
		for option in self.extra_options:
			name = option.split("=", maxsplit=1)[0]
			if name in _RESERVED_OPTIONS:
				raise ValueError(f"extra_options cannot override {name}")

	def __call__(self, seed: int, scenario: Scenario | None = None) -> MatchRecord:
		if scenario is not None:
			raise ValueError(
				"Arena CLI cannot initialize arbitrary scenarios; use a custom executor"
			)

		command = [
			self.executable,
			"match",
			self.bot,
			*self.extra_options,
			"--vs",
			self.opponent,
			"--seed",
			str(seed),
			"--format",
			"json",
		]
		completed = run_process(
			command,
			capture_output=True,
			text=True,
			check=False,
			timeout=self.timeout_seconds,
		)
		if completed.returncode != 0:
			detail = completed.stderr.strip() or completed.stdout.strip()
			raise RuntimeError(
				f"Arena CLI failed for seed {seed} with exit code "
				f"{completed.returncode}: {detail}"
			)
		try:
			payload = json.loads(completed.stdout)
		except json.JSONDecodeError as error:
			raise RuntimeError("Arena CLI returned invalid JSON") from error

		matches = payload.get("matches") if isinstance(payload, dict) else None
		if not isinstance(matches, list) or len(matches) != 1:
			raise RuntimeError("Arena CLI JSON must contain exactly one match")
		match = matches[0]
		if not isinstance(match, dict):
			raise RuntimeError("Arena CLI match result must be an object")
		if match.get("seed") != seed:
			raise RuntimeError(f"Arena CLI returned a result for the wrong seed: {seed}")

		replay = match.get("replay")
		rounds = replay.get("rounds") if isinstance(replay, dict) else None
		if not isinstance(rounds, list):
			raise RuntimeError("Arena CLI JSON is missing the single-match replay")
		rounds_won = {self.bot: 0, self.opponent: 0}
		for round_result in rounds:
			if not isinstance(round_result, dict):
				continue
			winner_id = round_result.get("winner_id")
			if winner_id == "p0":
				rounds_won[self.bot] += 1
			elif winner_id == "p1":
				rounds_won[self.opponent] += 1

		final_scores = match.get("final_scores", {})
		if not isinstance(final_scores, dict):
			final_scores = {}
		winner_id = match.get("winner_id")
		winner = self.bot if winner_id == "p0" else self.opponent if winner_id == "p1" else None
		return MatchRecord(
			seed=seed,
			winner=winner,
			winner_known="winner_id" in match,
			scores={
				self.bot: final_scores["p0"],
				self.opponent: final_scores["p1"],
			}
			if "p0" in final_scores and "p1" in final_scores
			else {},
			rounds_won=rounds_won,
			turns=(
				match["steps_played"]
				if isinstance(match.get("steps_played"), int)
				else None
			),
			metadata={
				"reason": match.get("reason"),
				"opponent_id": match.get("opponent_id"),
				"p0_starts": match.get("p0_starts"),
				"decision_time_ms_available": False,
			},
		)