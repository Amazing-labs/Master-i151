"""Translation between the Arena SDK types and the bot's domain types.

This is the only module that reads `PlayerView` fields or engine cards; the
rest of the bot works on `GameState` and `cards.Card`.
"""

from __future__ import annotations

from i151_engine.models.action import Action, ActionType

from cards import Card, Rank, Suit
from game_state import GameState, PlayerState, TableState, TurnState

_CARD_CACHE: dict[object, Card] = {}


def to_suit(engine_suit) -> Suit | None:
    """Engine suit -> domain suit (enum members share the same names)."""
    if engine_suit is None:
        return None
    return Suit[engine_suit.name]


def to_card(engine_card) -> Card:
    """Engine card -> domain card (enum members share the same names)."""
    card = _CARD_CACHE.get(engine_card)
    if card is None:
        card = Card(Rank[engine_card.rank.name], Suit[engine_card.suit.name])
        _CARD_CACHE[engine_card] = card
    return card


def to_cards(engine_cards) -> list[Card]:
    return [to_card(card) for card in engine_cards]


def action_cards(action: Action) -> tuple[Card, ...]:
    """Domain cards placed by a play action, in play order."""
    if action.type == ActionType.PLAY_CARD:
        return (to_card(action.card),) if action.card is not None else ()
    if action.type == ActionType.PLAY_MULTIPLE_CARDS:
        return tuple(to_card(card) for card in action.cards or ())
    return ()


def to_game_state(view) -> GameState:
    """Build the bot's observable state from a `PlayerView`."""
    you = view.you
    hand = to_cards(you.hand)
    you_state = PlayerState(
        hand=hand,
        hand_points=you.hand_points,
        total_score=you.total_score,
        hand_size=you.hand_size,
        is_chaining=you.is_chaining,
        consecutive_round_wins=you.consecutive_round_wins,
    )

    opponent_state = PlayerState()
    if view.opponents:
        opponent = view.opponents[0]
        opponent_state = PlayerState(
            total_score=opponent.total_score,
            hand_size=opponent.hand_size,
            consecutive_round_wins=opponent.consecutive_round_wins,
        )

    table = view.table
    recent = to_cards(table.recent_cards)
    table_state = TableState(
        recent_cards=recent,
        top_card=recent[-1] if recent else None,
        required_suit=to_suit(table.required_suit),
        ace_effect_active=table.ace_effect_active,
        bank_size=table.bank_size,
        played_pile_size=table.played_pile_size,
        last_play_cards=to_cards(table.last_play_cards),
        must_choose_suit=table.must_choose_suit,
    )

    turn = view.turn
    turn_state = TurnState(
        is_your_turn=turn.is_your_turn,
        can_draw=turn.can_draw,
        can_pass=turn.can_pass,
        draw_count_if_draw=turn.draw_count_if_draw,
    )

    match = view.match
    return GameState(
        you=you_state,
        opponent=opponent_state,
        table=table_state,
        turn=turn_state,
        target_score=match.target_score,
        round_number=match.round_number,
        round_active=True,
        player_count=match.player_count,
        active_player_count=match.active_player_count,
        step_index=turn.step_index,
    )
