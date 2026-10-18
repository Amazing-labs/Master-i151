"""Fast round simulator for the search: a faithful copy of the engine rules.

Mirrors i151_engine.core.legal_actions and i151_engine.core.reducer (0.2.4)
on integer cards and a mutable state, about an order of magnitude faster than
the engine's immutable dataclasses. Including the engine bug that duplicates
the played pile when a duel round ends on a Queen with an empty bank: the
simulator must play the real game. tests/test_fastsim.py replays random games
in both and compares every state.

Cards are ints: suit * 8 + rank, with the engine's enum orders.
Actions are tuples: (PLAY, card), (SUIT, suit), (DRAW,), (PASS,).
"""

from __future__ import annotations

from i151_engine.models.card import Rank, Suit

SUITS = tuple(Suit)
RANKS = tuple(Rank)
EIGHT = RANKS.index(Rank.EIGHT)
ACE = RANKS.index(Rank.ACE)
QUEEN = RANKS.index(Rank.QUEEN)
POINTS = tuple(rank.points for rank in RANKS)
CARD_POINTS = tuple(POINTS[card % 8] for card in range(32))

PLAY, SUIT, DRAW, PASS = 0, 1, 2, 3
NO_CARD = -1
NO_SUIT = -1


def card_id(engine_card) -> int:
    return SUITS.index(engine_card.suit) * 8 + RANKS.index(engine_card.rank)


def suit_of(card: int) -> int:
    return card // 8


def rank_of(card: int) -> int:
    return card % 8


def can_play_on(card: int, other: int) -> bool:
    rank = card % 8
    if rank == EIGHT:
        return True
    if other % 8 == ACE:
        return rank == ACE or rank == EIGHT
    if card // 8 == other // 8:
        return True
    return rank == other % 8


def can_play(card: int, top: int, required: int) -> bool:
    if card % 8 == EIGHT:
        return True
    if required != NO_SUIT:
        return card // 8 == required
    if top == NO_CARD:
        return True
    if top % 8 == EIGHT:
        return False
    return can_play_on(card, top)


class SimState:
    __slots__ = (
        "hands", "current", "top", "required", "choose", "ace", "skip",
        "bank", "pile", "last_count", "drawn", "chaining", "ended", "winner",
    )

    def __init__(self, hands, current, top, required, choose, ace, skip, bank, pile, last_count, drawn, chaining):
        self.hands = hands            # list[list[int]] per seat
        self.current = current
        self.top = top
        self.required = required
        self.choose = choose
        self.ace = ace
        self.skip = skip
        self.bank = bank              # list[int], drawn from the front
        self.pile = pile              # list[int], last = most recent
        self.last_count = last_count
        self.drawn = drawn            # list[bool] per seat
        self.chaining = chaining      # list[bool] per seat
        self.ended = False
        self.winner = -1

    def copy(self) -> SimState:
        state = SimState.__new__(SimState)
        state.hands = [list(hand) for hand in self.hands]
        state.current = self.current
        state.top = self.top
        state.required = self.required
        state.choose = self.choose
        state.ace = self.ace
        state.skip = self.skip
        state.bank = list(self.bank)
        state.pile = list(self.pile)
        state.last_count = self.last_count
        state.drawn = list(self.drawn)
        state.chaining = list(self.chaining)
        state.ended = self.ended
        state.winner = self.winner
        return state


def from_engine(round_state) -> SimState:
    """Copy an engine RoundState (tests and debugging)."""
    def ids(cards):
        return [card_id(card) for card in cards]

    players = round_state.players
    state = SimState(
        hands=[ids(player.hand) for player in players],
        current=round_state.current_player_index,
        top=card_id(round_state.top_card) if round_state.top_card is not None else NO_CARD,
        required=SUITS.index(round_state.required_suit) if round_state.required_suit is not None else NO_SUIT,
        choose=round_state.choose_suit,
        ace=round_state.ace_effect_active,
        skip=round_state.skip_next_player,
        bank=ids(round_state.bank),
        pile=ids(round_state.played_pile),
        last_count=round_state.last_play_count,
        drawn=[player.has_drawn_this_turn for player in players],
        chaining=[player.is_chaining for player in players],
    )
    state.ended = round_state.phase.value == "ended"
    state.winner = next(
        (i for i, player in enumerate(players) if player.player_id == round_state.round_winner_id), -1
    )
    return state


def to_action_tuple(engine_action) -> tuple:
    kind = engine_action.type.value
    if kind == "playCard":
        return (PLAY, card_id(engine_action.card))
    if kind == "chooseSuit":
        return (SUIT, SUITS.index(engine_action.chosen_suit))
    if kind == "drawCard":
        return (DRAW,)
    if kind == "passTurn":
        return (PASS,)
    raise ValueError(f"Unsupported action: {engine_action}")


def legal_actions(s: SimState) -> list[tuple]:
    if s.ended:
        return []
    p = s.current
    hand = s.hands[p]
    top = s.top
    if top == NO_CARD and s.required == NO_SUIT:
        playable = list(hand)
    else:
        playable = [card for card in hand if can_play(card, top, s.required)]
    if s.chaining[p] and top != NO_CARD:
        playable = [card for card in playable if card % 8 == top % 8]

    actions = [(PLAY, card) for card in playable]
    if s.choose and top != NO_CARD and top % 8 == EIGHT:
        actions.extend((SUIT, suit) for suit in range(4))
    if top != NO_CARD and not s.choose:
        actions.append((PASS,) if s.drawn[p] or s.chaining[p] else (DRAW,))
    if top == NO_CARD and not s.choose:
        if s.drawn[p] or s.chaining[p]:
            actions.append((PASS,))
        elif not actions:
            actions.append((DRAW,))
    return actions


def apply(s: SimState, action: tuple) -> None:
    """Apply a legal action in place."""
    kind = action[0]
    if kind == PLAY:
        _play(s, action[1])
    elif kind == DRAW:
        _draw(s)
    elif kind == PASS:
        _next_player(s, False)
    else:
        p = s.current
        s.chaining[p] = False
        s.required = action[1]
        s.choose = False
        _next_player(s, False)


def _play(s: SimState, card: int) -> None:
    p = s.current
    hand = s.hands[p]
    rank = card % 8
    previous_top = s.top
    hand.remove(card)
    s.pile.append(card)

    same_rank_left = False
    for other in hand:
        if other % 8 == rank:
            same_rank_left = True
            break
    chaining = (
        ((previous_top != NO_CARD and previous_top % 8 == rank) or rank == EIGHT)
        and same_rank_left
    )
    s.drawn[p] = False
    s.chaining[p] = chaining
    s.top = card
    s.last_count = 1
    s.ace = False
    s.required = NO_SUIT
    s.choose = False

    if rank == EIGHT:
        s.choose = True
    elif rank == ACE:
        s.ace = True
    elif rank == QUEEN:
        s.skip = True

    if not hand:
        if len(s.hands) == 2 and rank == QUEEN:
            # Engine: _draw_from_bank drops the refilled pile -> duplication.
            bank = s.bank
            if len(bank) < 1 and s.pile:
                bank.extend(s.pile)
            if bank:
                hand.append(bank.pop(0))
            s.drawn[p] = True
            s.chaining[p] = False
            _next_player(s, True)
            return
        s.ended = True
        s.winner = p
        return

    if not s.chaining[p] and not s.choose:
        _next_player(s, False)


def _draw(s: SimState) -> None:
    p = s.current
    if s.drawn[p]:
        _next_player(s, False)
        return
    count = 2 if s.ace else 1
    bank = s.bank
    if len(bank) < count and s.pile:
        bank.extend(s.pile)
        s.pile = []
    hand = s.hands[p]
    for _ in range(count):
        if not bank:
            break
        hand.append(bank.pop(0))
    s.last_count = 0
    if s.ace:
        s.ace = False
        _next_player(s, False)
        return
    s.drawn[p] = True
    if not bank and not s.pile:
        s.top = NO_CARD
        s.required = NO_SUIT


def _next_player(s: SimState, drawn: bool) -> None:
    p = s.current
    s.drawn[p] = drawn
    s.chaining[p] = False
    s.choose = False
    n = len(s.hands)
    nxt = (p + 1) % n
    if s.skip:
        nxt = (nxt + 1) % n
        s.skip = False
    s.current = nxt
