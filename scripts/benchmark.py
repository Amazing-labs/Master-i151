"""Paired Arena benchmarks, meant to run inside the Docker image (isolated mode).

Development tooling only: never import this from bot.py.

Protocol (see docs/experiments.md):
- `--random --seed PANEL`: reproducible panel of independent seeds. Consecutive
  seeds share most of their deals, so they must not be used.
- every seed is played once with each starting player (p0, then p1);
- 400 ms per decision, the competition limit;
- bots are compared pairwise on identical (seed, starter) games.

Usage:
    python scripts/benchmark.py run BOT [--vs medium] [--panel 777] [--games 1000] [--label NAME]
    python scripts/benchmark.py compare LABEL_A LABEL_B [--vs medium] [--panel 777]

Results are written to experiments/<label>_<opponent>_<panel>_<starter>.json.

Why not `arena match --isolated --games N`: the CLI keeps one worker process
per bot for the whole series and sends it a new `setup` before every match.
`install_competition_sandbox` is not idempotent, so each match stacks another
import/filesystem guard on the worker and the cost per game grows linearly
(about 2.8 h for 1000 games). This script replays the CLI loop with the same
seeds, dealer choice and `play_bots_match` call, but tears the workers down
after every match so each one starts from a fresh process.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RESULTS_DIR = Path("experiments")
STARTERS = ("p0", "p1")
DECISION_TIMEOUT_MS = 400
CHUNK_SIZE = 25


def _result_path(label: str, opponent: str, panel: int, starter: str) -> Path:
    return RESULTS_DIR / f"{label}_{opponent}_{panel}_{starter}.json"


def _load_wins(label: str, opponent: str, panel: int) -> tuple[dict, list]:
    wins, anomalies = {}, []
    for starter in STARTERS:
        path = _result_path(label, opponent, panel, starter)
        for match in json.loads(path.read_text(encoding="utf-8"))["matches"]:
            wins[(match["seed"], starter)] = 1 if match["winner_id"] == "p0" else 0
            if match["reason"] != "normal":
                anomalies.append((match["seed"], starter, match["reason"], match["winner_id"]))
    return wins, anomalies


def _rate_line(label: str, wins: dict, anomalies: list) -> str:
    n = len(wins)
    p = sum(wins.values()) / n
    margin = 1.96 * math.sqrt(p * (1 - p) / n)
    return f"{label}: {p:.1%} ± {margin:.1%} (n={n}) anomalies={anomalies}"


def _play_chunk(bot_file: str, opponent_spec: str, starter: str, seeds: list[int]) -> list[dict]:
    """Play `seeds` in isolated mode, with fresh worker processes for every match."""
    # Pinned SDK (0.2.10): these private helpers are the ones `arena match` uses.
    from arena_sdk.cli import _dealer_for_game
    from arena_sdk.opponents import load_resolved_submission, resolve_opponent_arg
    from i151_engine.runner.config import MatchConfig
    from i151_engine.runner.match_runner import play_bots_match

    bot, challenger_dir = load_resolved_submission(Path(bot_file), isolated=True)
    opponent = resolve_opponent_arg(opponent_spec, isolated=True)
    opponent_dir = opponent.submission_dir or Path(".")

    rows = []
    for seed in seeds:
        dealer, p0_starts = _dealer_for_game(starter=starter, p0_first_rate=None, match_seed=seed)
        bot.setup(challenger_dir)
        opponent.bot.setup(opponent_dir)
        try:
            result = play_bots_match(
                bot,
                opponent.bot,
                MatchConfig(seed=seed, initial_dealer_index=dealer, decision_timeout_ms=DECISION_TIMEOUT_MS),
                challenger_name=challenger_dir.name,
                opponent_name=opponent.name,
                opponent_id=opponent.opponent_id,
                challenger_dir=challenger_dir,
                opponent_dir=opponent.submission_dir,
                manage_lifecycle=False,
            )
        finally:
            bot.teardown()
            opponent.bot.teardown()
        rows.append({
            "seed": seed,
            "winner_id": result.winner_id,
            "reason": result.reason,
            "forfeited_player_id": result.forfeited_player_id,
            "final_scores": result.final_scores,
            "rounds_played": result.rounds_played,
            "steps_played": result.steps_played,
            "p0_starts": p0_starts,
        })
    return rows


def run(args: argparse.Namespace) -> None:
    from arena_sdk.cli import _match_seeds

    label = args.label or Path(args.bot).stem
    RESULTS_DIR.mkdir(exist_ok=True)
    seeds = _match_seeds(base_seed=args.panel, games=args.games, randomize=True)
    chunks = [seeds[i:i + CHUNK_SIZE] for i in range(0, len(seeds), CHUNK_SIZE)]

    # Run from a container-local copy (the Windows bind mount is slow). The
    # sibling modules are copied too, since the SDK loads flat local imports;
    # the entry file becomes bot.py, as in a submission.
    entry = Path(args.bot)
    workdir = Path(tempfile.mkdtemp(prefix="bench-")) / label
    workdir.mkdir()
    for module in entry.parent.glob("*.py"):
        shutil.copyfile(module, workdir / module.name)
    bot_file = workdir / "bot.py"
    shutil.copyfile(entry, bot_file)

    for starter in STARTERS:
        rows: list[dict] = []
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(_play_chunk, str(bot_file), args.vs, starter, chunk) for chunk in chunks]
            for future in futures:
                rows.extend(future.result())
                print(f"{label} starter={starter}: {len(rows)}/{len(seeds)}", flush=True)
        wins = sum(1 for row in rows if row["winner_id"] == "p0")
        payload = {"summary": {"games": len(rows), "wins": wins}, "matches": rows}
        _result_path(label, args.vs, args.panel, starter).write_text(
            json.dumps(payload, indent=1), encoding="utf-8"
        )
    print(_rate_line(label, *_load_wins(label, args.vs, args.panel)))


def compare(args: argparse.Namespace) -> None:
    a, anomalies_a = _load_wins(args.label_a, args.vs, args.panel)
    b, anomalies_b = _load_wins(args.label_b, args.vs, args.panel)
    if a.keys() != b.keys():
        sys.exit("The two runs do not cover the same (seed, starter) games.")

    print(_rate_line(args.label_a, a, anomalies_a))
    print(_rate_line(args.label_b, b, anomalies_b))

    diffs = [a[key] - b[key] for key in a]
    n = len(diffs)
    mean = sum(diffs) / n
    sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / (n - 1))
    print(
        f"{args.label_a} - {args.label_b}: {mean:+.1%} ± {1.96 * sd / math.sqrt(n):.1%} (95% CI) | "
        f"won only by {args.label_a}: {diffs.count(1)}, only by {args.label_b}: {diffs.count(-1)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(required=True)

    run_parser = sub.add_parser("run", help="benchmark one bot on a panel")
    run_parser.add_argument("bot")
    run_parser.add_argument("--label")
    run_parser.set_defaults(func=run)

    compare_parser = sub.add_parser("compare", help="paired comparison of two runs")
    compare_parser.add_argument("label_a")
    compare_parser.add_argument("label_b")
    compare_parser.set_defaults(func=compare)

    for p in (run_parser, compare_parser):
        p.add_argument("--vs", default="medium")
        p.add_argument("--panel", type=int, default=777)
    run_parser.add_argument("--games", type=int, default=1000)
    run_parser.add_argument("--jobs", type=int, default=4, help="parallel match processes")

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
