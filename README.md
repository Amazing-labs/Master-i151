# Master-i151

Bot for the i151 Arena challenge.

## Team

- Dioman KeÃ¯ta â€” GameState & Knowledge
- KantÃ© â€” Rules & Actions
- Maiga â€” Strategy & Evaluation
- Diarra â€” Simulation & Analysis

## Architecture

\\\
PlayerView
    â†“
Arena Adapter
    â†“
GameState
    â†“
Rules / Actions
    â†“
Strategy / Evaluator
    â†“
Decision
    â†“
Action
\\\

## Laboratory

\\\
Replay
    â†“
Analysis
    â†“
Hypothesis
    â†“
Experiment
    â†“
Validated Pattern
    â†“
Strategy
\\\

## Development

The production bot must remain independent from the analysis and
simulation tooling.

The competition entry point is:

\\\
bot.py
\\\
