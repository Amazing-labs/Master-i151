"""KnowledgeEngine: unit cases and a check against the engine's hidden state."""

from __future__ import annotations

import random
from dataclasses import replace

import pytest
from i151_engine.core.legal_actions import legal_actions
from i151_engine.core.reducer import apply_action
from i151_engine.core.scoring import apply_round_scoring
from i151_engine.game.round import create_match, start_round
from i151_engine.models.enums import MatchStatus, RoundPhase
from i151_engine.view.builder import build_player_view

from arena_adapter import to_card, to_game_state
from cards import Card, Rank, Suit
from game_state import GameState, PlayerState, TableState
from knowledge import KnowledgeEngine

AS = Card(Rank.ACE, Suit.SPADES)
KS = Card(Rank.KING, Suit.SPADES)
QS = Card(Rank.QUEEN, Suit.SPADES)
JS = Card(Rank.JACK, Suit.SPADES)
TH = Card(Rank.TEN, Suit.HEARTS)


def _state(pile_size, recent, *, hand=(TH,), round_number=1, step=0, opponent=5, bank=10):
    return GameState(
        you=PlayerState(hand=list(hand), hand_size=len(hand)),
        opponent=PlayerState(hand_size=opponent),
        table=TableState(recent_cards=list(recent), played_pile_size=pile_size, bank_size=bank),
        round_number=round_number,
        step_index=step,
    )


def test_pile_is_rebuilt_from_successive_tails():
    k = KnowledgeEngine()
    k.observe(_state(1, [AS], step=1))
    k.observe(_state(3, [AS, KS, QS], step=2))
    k.observe(_state(4, [KS, QS, JS], step=3))
    assert k.pile == [AS, KS, QS, JS]
    assert k.unknown_pile_count() == 0
    assert k.knows(AS) and k.knows(TH)
    assert not k.may_be_in_opponent_hand(AS)


def test_missed_plays_stay_unknown():
    k = KnowledgeEngine()
    k.observe(_state(1, [AS], step=1))
    k.observe(_state(5, [KS, QS, JS], step=2))
    assert k.pile == [AS, None, KS, QS, JS]
    assert k.unknown_pile_count() == 1


def test_pile_shuffled_back_into_bank_is_forgotten():
    k = KnowledgeEngine()
    k.observe(_state(3, [AS, KS, QS], step=1))
    k.observe(_state(1, [JS], step=2))
    assert k.pile == [JS]
    assert k.is_unknown(AS)


def test_new_round_and_new_match_reset_the_knowledge():
    k = KnowledgeEngine()
    k.observe(_state(2, [AS, KS], round_number=1, step=10))
    k.observe(_state(0, [], round_number=2, step=11))
    assert k.pile == []
    k.observe(_state(1, [QS], round_number=2, step=12))
    k.observe(_state(0, [], round_number=2, step=1))
    assert k.pile == []


def test_opponent_probability_is_uniform_over_unknown_cards():
    k = KnowledgeEngine()
    k.observe(_state(1, [AS], hand=(TH,), opponent=6))
    assert k.unknown_card_count() == 30
    assert k.opponent_probability(KS) == pytest.approx(6 / 30)
    assert k.opponent_probability(AS) == 0.0
    assert k.opponent_probability(TH) == 0.0


# ---------------------------------------------------------------------------
# Against the engine's hidden state, fed exactly like the SDK does:
# a decide view when p0 is to move, an observe view after each p1 action.
# ---------------------------------------------------------------------------


def _random_match_views(seed: int):
    """Yield (view for p0, hidden round state) as the SDK would deliver them."""
    rng = random.Random(seed)
    match = create_match(("A", "B"), seed=seed)
    steps = 0
    while match.status == MatchStatus.IN_PROGRESS and steps < 5000:
        round_state = match.current_round
        if round_state.phase == RoundPhase.ENDED:
            match = apply_round_scoring(match, round_state.round_winner_id)
            if match.status == MatchStatus.FINISHED:
                return
            match = start_round(match)
            continue
        steps += 1
        actor = round_state.current_player.player_id
        if actor == "p0":
            yield build_player_view(match, round_state, "p0", opponent_specs={}, step_index=steps), round_state
        new_round = apply_action(round_state, rng.choice(legal_actions(round_state)))
        match = replace(match, current_round=new_round)
        if actor == "p1":
            yield build_player_view(match, new_round, "p0", opponent_specs={}, step_index=steps), new_round


def _card_count(round_state) -> int:
    return (
        len(round_state.bank)
        + len(round_state.played_pile)
        + sum(len(player.hand) for player in round_state.players)
    )


@pytest.mark.integration
def test_knowledge_never_contradicts_the_engine():
    observations = 0
    for seed in range(40):
        k = KnowledgeEngine()
        for view, truth in _random_match_views(seed):
            k.observe(to_game_state(view))
            # Engine bug (rules.RULES_REGISTRY["engine_duplicates_pile_on_queen_finish"]):
            # the deck can hold duplicated cards until the round ends.
            if _card_count(truth) != 32:
                continue
            observations += 1

            true_pile = [to_card(card) for card in truth.played_pile]
            assert len(k.pile) == len(true_pile)
            for known, actual in zip(k.pile, true_pile):
                assert known is None or known == actual

            hidden = {to_card(c) for c in truth.bank} | {
                to_card(c) for c in truth.player_by_id("p1").hand
            }
            assert hidden <= k.unknown_cards
            assert len(k.unknown_cards) == len(hidden) + k.unknown_pile_count()
    assert observations > 10_000


@pytest.mark.integration
def test_pile_is_fully_known_when_fed_every_step():
    for seed in range(40):
        k = KnowledgeEngine()
        for view, _truth in _random_match_views(seed):
            k.observe(to_game_state(view))
            assert k.unknown_pile_count() == 0
