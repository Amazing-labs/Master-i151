"""fastsim must play exactly the engine's game: same legal actions, same states."""

from __future__ import annotations

import random
from dataclasses import replace

import pytest
from i151_engine.core.legal_actions import legal_actions
from i151_engine.core.reducer import apply_action
from i151_engine.core.scoring import apply_round_scoring
from i151_engine.game.round import create_match, start_round
from i151_engine.models.enums import MatchStatus, RoundPhase

import fastsim

pytestmark = pytest.mark.integration


def _snapshot(s: fastsim.SimState):
    return (
        [sorted(hand) for hand in s.hands],
        s.current, s.top, s.required, s.choose, s.ace, s.skip,
        list(s.bank), list(s.pile), s.last_count,
        list(s.drawn), list(s.chaining), s.ended, s.winner,
    )


def test_fastsim_replays_random_games_exactly():
    steps = 0
    for seed in range(150):
        rng = random.Random(seed)
        match = create_match(("A", "B"), seed=seed)
        sim = fastsim.from_engine(match.current_round)
        while match.status == MatchStatus.IN_PROGRESS and steps < 2_000_000:
            round_state = match.current_round
            if round_state.phase == RoundPhase.ENDED:
                match = apply_round_scoring(match, round_state.round_winner_id)
                if match.status == MatchStatus.FINISHED:
                    break
                match = start_round(match)
                sim = fastsim.from_engine(match.current_round)
                continue

            engine_legal = legal_actions(round_state)
            assert sorted(fastsim.to_action_tuple(a) for a in engine_legal) == sorted(fastsim.legal_actions(sim))

            action = rng.choice(engine_legal)
            new_round = apply_action(round_state, action)
            fastsim.apply(sim, fastsim.to_action_tuple(action))
            assert _snapshot(sim) == _snapshot(fastsim.from_engine(new_round)), (seed, action)

            match = replace(match, current_round=new_round)
            steps += 1
    assert steps > 100_000
