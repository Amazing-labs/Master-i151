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
| `tests/` | Unit and engine integration tests |
| `docs/experiments.md` | Benchmark protocol and results |

## Tests

```powershell
python -m pytest tests                     # all tests
python -m pytest tests -m "not integration"  # skip engine integration tests
```

`pytest` is a development tool only; it is not a bot dependency.
