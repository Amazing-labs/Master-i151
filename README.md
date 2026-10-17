# Master-i151

Bot for the i151 Arena challenge.

## Architecture

```text
PlayerView
↓
Arena Adapter
↓
GameState
↓
Rules / Actions
↓
Strategy / Evaluator
↓
Decision
↓
Action
```

## Laboratory

```text
Replay
↓
Analysis
↓
Hypothesis
↓
Experiment
↓
Validated Pattern
↓
Strategy
```

## Development

The production bot must remain independent from the analysis and
simulation tooling.

The competition entry point is:

`bot.py`

`bot.py` is currently self-contained: it does not import the `src/` packages
yet. `arena pack` only bundles `bot.py` and its local imports.

## Project layout

| Path | Content |
| ---- | ------- |
| `bot.py` | Competition bot (V2.3) |
| `archive/bots/` | Previous bot versions |
| `src/domain/game/` | Observable game state and card knowledge |
| `src/domain/rules/` | Action classification, rule registry and legality checks (rule notes in `RULES.md`) |
| `src/domain/strategy/` | Evaluation and minimax search |
| `simulation/` | Seeded batch runs and the Arena CLI executor (development only) |
| `scripts/` | Isolated-mode benchmark tooling (development only) |
| `tests/` | Unit and engine integration tests |
| `docs/experiments.md` | Benchmark protocol and results |

## Tests

```powershell
python -m pytest tests                     # all tests
python -m pytest tests -m "not integration"  # skip engine integration tests
```

`pytest` is a development tool only; it is not a bot dependency.

## Benchmarks (isolated mode)

The competition runs each bot in an isolated child process. That mode
(`arena match --isolated`) does not work on Windows, so benchmarks run in a
Linux Docker image with Python 3.12, `i151-arena-sdk 0.2.10` and
`i151-engine 0.2.4` pinned (`Dockerfile`). Docker Desktop is required.

```powershell
.\scripts\bench.ps1 run bot.py --vs medium --panel 777 --games 1000
.\scripts\bench.ps1 run archive/bots/bot_v2_1.py --vs medium --panel 777 --games 1000
.\scripts\bench.ps1 compare bot bot_v2_1 --vs medium --panel 777
```

Each run plays every seed of a random panel once per starting player, with
a 400 ms decision limit, and writes its results to `experiments/` (ignored by
git). `compare` prints a paired difference with its 95% confidence interval.
See `docs/experiments.md` for the protocol.

The script does not call `arena match --isolated --games N` directly: with SDK
0.2.10 that command reuses one worker per bot for the whole series and stacks
a new sandbox layer on it before every match, so each game gets slower than
the previous one. `scripts/benchmark.py` runs the same match loop with a fresh
worker per match and produces the same games, seed for seed.
