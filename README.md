# Master-i151

Rule-based bot for the [i151 Arena](https://challenge.jeu-151.com) challenge,
written in Python on top of the official SDK (`i151-arena-sdk 0.2.10`,
`i151-engine 0.2.4`). No machine learning: explicit heuristics, validated
with reproducible paired benchmarks.

## Status

The competition bot (`bot/`) plays the V2.3 strategy. Against the public
`medium` example bot, on 2000 games per panel (random seeds, both starting
players):

| Panel | Win rate | vs previous version (V2.1), paired |
| ----- | -------: | ---------------------------------: |
| 2026 (development) | 54.2% ± 2.2 | +4.1 ± 2.1 points |
| 777 (confirmation) | 59.7% ± 2.1 | +5.6 ± 2.0 points |

Against `basic`: 81.8% ± 1.7. In isolated mode (the competition mode), panel
777 gives the same games with no timeout or forfeit. Full protocol and
history: [`docs/experiments.md`](docs/experiments.md).

`medium` is a public example; the strength of the real competitors is
unknown.

## Quick start

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install i151-arena-sdk==0.2.10 i151-engine==0.2.4 pytest

arena test bot/bot.py                                  # official smoke test
arena match bot/bot.py --vs medium --games 20 --seed 1 --random --format summary
arena pack bot                                         # submission ZIP
```

`pytest` is a development tool only. `arena_sdk` and `i151_engine` are
provided by the Arena sandbox; `arena pack` strips them from
`requirements.txt`.

## How the bot decides

```text
PlayerView ──arena_adapter──> GameState ──> KnowledgeEngine.observe
legal_actions ──actions (classification)──> strategy.Options
StrategyEngine.decide ──> Decision (index) ──> legal Action ──> validators.ensure_legal
```

| Module (`bot/`) | Role |
| --------------- | ---- |
| `bot.py` | SDK contract: `setup` (new match), `observe` (after each opponent action), `decide` |
| `decision_service.py` | The pipeline above |
| `arena_adapter.py` | The only module that reads SDK and engine types |
| `cards.py`, `game_state.py` | Domain cards and the observable game state |
| `knowledge.py` | Our hand, the played pile tracked card by card, unknown cards (bank + opponent hand) and uniform opponent probabilities; reset every round |
| `rules.py` | Rule registry with confidence levels (RULE / FACT / HYPOTHESIS / UNKNOWN) and card playability |
| `actions.py`, `validators.py` | Legal action classification and the final legality guard |
| `strategy.py`, `weights.py` | Strategy engine and its tunable weights |

Design rules:

- **Never build an action.** The strategy returns an index into the options
  the engine declared legal; `validators.ensure_legal` checks the result.
- **Only observable information.** The opponent's hand is never read; the
  knowledge engine exposes unknown cards and probabilities, not guesses
  presented as facts.
- **One source of truth for rules.** Playability in `rules.py` is checked
  against the engine on every card, top card and required suit
  (`tests/rules/test_playability.py`).
- **Knowledge must never cost a match.** A failure in `observe` or in the
  knowledge update is caught; the decision still happens.

The V2.3 heuristics score a play by the best sequence it opens within the
same turn (same-rank chaining, Queen extra turn in a duel), hold eights early
and dump them late, use aces when we cannot follow the suit, and choose the
suit we hold most after an eight. `tests/test_parity.py` checks that `bot/`
takes exactly the decisions of `archive/bots/bot_v2_3.py`. The knowledge
engine is wired but not yet used by the heuristics.

## Game rules in brief

Verified in the engine source (details and sources in
[`docs/game-rules.md`](docs/game-rules.md) and `rules.RULES_REGISTRY`):

- 32 cards, 8 per player. Points: 8 = 32, A = 11, 10 = 10, 9 = 9, 7 = 7,
  K = 4, Q = 3, J = 2.
- Every action plays **one** card; `PLAY_MULTIPLE_CARDS` is never offered.
  A turn can still hold several cards: same-rank chaining, or a Queen in a
  duel (the opponent is skipped).
- An eight is always playable and is followed by a suit choice. On an ace,
  only an ace or an eight can be played; the next player otherwise draws two.
- Finishing a duel round on a Queen makes you draw instead of winning.
- Round losers add the points left in their hand; three round wins in a row
  give -10. A player reaching 151 is eliminated.
- **Engine bug (0.2.4):** finishing on a Queen in a duel with an empty bank
  duplicates the played pile (32 → 60 cards until the round ends).

## Submission constraints

- **Flat modules only.** The SDK loader resolves a local import only as a
  `name.py` file next to `bot.py`; packages are rejected with
  `ModuleNotFoundError`. Every production module therefore lives flat in
  `bot/` and is imported as `from cards import Card`, never relatively.
- **Forbidden at runtime** (sandbox): `os`, `subprocess`, `socket`, `pickle`,
  `importlib`, `asyncio`, `gc`, `signal`, `multiprocessing` and others; see
  `FORBIDDEN_RUNTIME_IMPORTS` in `arena_sdk/ipc/sandbox.py`. The bot only
  uses `dataclasses`, `enum`, `collections` and `typing`.
- **400 ms per decision** (competition rules). Current latency: median
  0.13 ms, maximum 25 ms.
- Illegal action, crash or timeout means a forfeit.

## Tests

```powershell
python -m pytest tests                       # everything (about 35 s)
python -m pytest tests -m "not integration"  # unit tests only (under 1 s)
```

Integration tests play real engine games: legality of every real action,
knowledge checked against the engine's hidden state, and decision parity
with V2.3.

## Benchmarks

A strategy change is kept only if a **paired** benchmark shows it, on a
panel that was not used to tune it. Rules of the protocol:

- Use random seed panels (`--random --seed PANEL`), never consecutive seeds:
  round `r` of seed `s` is dealt with `Random(s + r)`, so consecutive seeds
  share most of their deals.
- Play every seed once per starting player and compare bots game by game.
- Use the 400 ms decision limit.

The competition runs each bot in an isolated process. That mode fails on
Windows, so benchmarks run in a pinned Linux image (`Dockerfile`, Python
3.12). Docker Desktop is required.

```powershell
.\scripts\bench.ps1 run bot/bot.py --vs medium --panel 777 --games 1000
.\scripts\bench.ps1 run archive/bots/bot_v2_1.py --vs medium --panel 777 --games 1000
.\scripts\bench.ps1 compare bot bot_v2_1 --vs medium --panel 777
```

Results go to `experiments/` (ignored by git). The script does not use
`arena match --isolated --games N`: with SDK 0.2.10 that command reuses one
worker per bot and stacks a new sandbox layer on it before every match, so a
1000-game series takes hours. `scripts/benchmark.py` runs the same match loop
with a fresh worker per match and produces the same games.

## Repository layout

| Path | Content |
| ---- | ------- |
| `bot/` | Competition bot (flat modules) |
| `tests/` | Unit and engine integration tests (`conftest.py` puts `bot/` on the import path) |
| `scripts/` | Isolated benchmarks: `benchmark.py` (runs in Docker), `bench.ps1` (PowerShell wrapper) |
| `Dockerfile` | Pinned Linux runtime for isolated benchmarks |
| `archive/bots/` | Previous single-file bots (V1 to V2.3), kept as references |
| `simulation/` | Generic seeded batch runner and Arena CLI executor (development only) |
| `docs/experiments.md` | Benchmark protocol, results and untested ideas |
| `docs/game-rules.md` | Rule notes with confidence levels |
| `AGENT_BRIEFING.md` | Working rules for AI agents on this project |
| `analysis/`, `docs/architecture.md`, `docs/implementation-guide.md`, `docs/patterns.md` | Empty placeholders |

Development tooling (`scripts/`, `simulation/`, `tests/`) may use any
module; `bot/` must never import it.

## Team

Dioman Keïta, Kanté, Maïga and Diarra. Initial responsibilities: game state
and knowledge (Dioman), rules and actions (Kanté), strategy and evaluation
(Maïga), simulation and result analysis (Diarra).
