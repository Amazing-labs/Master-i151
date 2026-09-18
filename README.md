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
