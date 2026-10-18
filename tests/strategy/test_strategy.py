from __future__ import annotations

from cards import Card, Rank, Suit
from game_state import GameState, PlayerState, TableState
from knowledge import KnowledgeEngine
from strategy import DecisionKind, Options, StrategyEngine, turn_sequences


def c(code: str) -> Card:
    """'TD' -> ten of diamonds."""
    return Card(Rank(code[0]), Suit(code[1]))


def _state(hand, top=None, opponent=5) -> GameState:
    cards = [c(code) for code in hand]
    recent = [c(top)] if top else []
    return GameState(
        you=PlayerState(hand=cards, hand_size=len(cards)),
        opponent=PlayerState(hand_size=opponent),
        table=TableState(recent_cards=recent, top_card=recent[-1] if recent else None),
    )


def _plays(state: GameState):
    top = state.table.top_card
    from rules import can_play_with_required_suit

    return tuple((card,) for card in state.you.hand if can_play_with_required_suit(card, top, None))


def test_same_rank_chaining_opens_a_longer_sequence():
    state = _state(["7D", "KC", "JC", "TD", "9S", "AC", "7S", "TS"], top="TC")
    assert (c("TD"), c("TS")) in turn_sequences(state, c("TD"))


def test_engine_prefers_the_chain_over_the_ace():
    # Regression of the case found in replay-v2 (V2 played the ace).
    state = _state(["7D", "KC", "JC", "TD", "9S", "AC", "7S", "TS"], top="TC")
    plays = _plays(state)
    decision = StrategyEngine().decide(state, KnowledgeEngine(), Options(plays=plays))
    assert decision.kind is DecisionKind.PLAY
    assert plays[decision.index] == (c("TD"),)


def test_queen_in_a_duel_continues_on_a_playable_card():
    state = _state(["QS", "KS", "TH"], top="JS")
    assert (c("QS"), c("KS")) in turn_sequences(state, c("QS"))
    assert (c("QS"), c("TH")) not in turn_sequences(state, c("QS"))


def test_an_eight_ends_the_sequence():
    state = _state(["8S", "8H", "7S"], top="7H")
    assert turn_sequences(state, c("8S")) == [(c("8S"),)]


def test_queen_extra_turn_lets_us_go_out():
    state = _state(["QS", "KS"], top="JS", opponent=1)
    plays = _plays(state)
    decision = StrategyEngine().decide(state, KnowledgeEngine(), Options(plays=plays))
    assert plays[decision.index] == (c("QS"),)


def test_finishing_a_duel_on_a_queen_is_heavily_penalised():
    state = _state(["KS", "QS"], top="JS")
    engine = StrategyEngine()
    assert engine._sequence_score(state, (c("KS"), c("QS"))) == engine.weights.finishes_on_queen


def test_priorities_suit_then_play_then_pass_then_default():
    engine, k = StrategyEngine(), KnowledgeEngine()
    state = _state(["7S", "9S", "KH"])
    suits = (Suit.HEARTS, Suit.SPADES)
    assert engine.decide(state, k, Options(suits=suits, plays=((c("7S"),),))).kind is DecisionKind.CHOOSE_SUIT
    assert engine.decide(state, k, Options(plays=((c("7S"),),), can_pass=True)).kind is DecisionKind.PLAY
    assert engine.decide(state, k, Options(can_pass=True)).kind is DecisionKind.PASS
    assert engine.decide(state, k, Options()).kind is DecisionKind.DEFAULT


def test_suit_choice_follows_the_hand():
    state = _state(["7S", "9S", "KH"])
    suits = (Suit.HEARTS, Suit.SPADES, Suit.CLUBS)
    decision = StrategyEngine().decide(state, KnowledgeEngine(), Options(suits=suits))
    assert suits[decision.index] is Suit.SPADES
