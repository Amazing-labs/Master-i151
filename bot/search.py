"""Determinized Monte Carlo search over the fast rules simulator (fastsim).

For each decision:
1. sample `worlds`: the opponent's hand and the bank order are drawn
   uniformly from the cards the KnowledgeEngine still considers unknown
   (only observable information is used);
2. in every world, apply each legal action and play the round to its end
   with a fast greedy policy for both players;
3. keep the action with the best mean value. All actions are evaluated on the
   same worlds and random streams (common random numbers).

The value of a finished round is the score swing it causes (the loser adds
the points left in their hand), plus a large bonus or malus when it
eliminates a player.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

import fastsim
from fastsim import ACE, CARD_POINTS, EIGHT, NO_CARD, NO_SUIT, PASS, PLAY, QUEEN, SUIT, SimState
from knowledge import KnowledgeEngine


@dataclass(frozen=True, slots=True)
class SearchConfig:
    worlds: int = 64
    time_budget_ms: float = 150.0
    max_rollout_steps: int = 250
    elimination_value: float = 300.0
    rollout_policy: str = "heuristic"  # "heuristic" or "greedy"
    # HYPOTHESIS: the opponent always plays when it can (knowledge.opponent_excluded).
    infer_no_play: bool = False


class MonteCarloSearch:
    def __init__(self, config: SearchConfig = SearchConfig()) -> None:
        self.config = config

    def choose(self, view, legal_actions: list, knowledge: KnowledgeEngine, rng: random.Random) -> int | None:
        """Index of the best legal action, or None when the search cannot run."""
        if len(legal_actions) < 2 or len(view.opponents) != 1:
            return None

        started = time.perf_counter()
        budget = self.config.time_budget_ms / 1000.0
        candidates = [fastsim.to_action_tuple(action) for action in legal_actions]
        me = list(view.match.seats).index(view.you.player_id)
        totals = [0, 0]
        totals[me] = view.you.total_score
        totals[1 - me] = view.opponents[0].total_score
        target = view.match.target_score

        sums = [0.0] * len(candidates)
        worlds = 0
        while worlds < self.config.worlds:
            world = _sample_world(view, knowledge, me, rng, self.config.infer_no_play)
            if world is None:
                return None
            seed = rng.random()
            for index, action in enumerate(candidates):
                state = world.copy()
                fastsim.apply(state, action)
                sums[index] += self._rollout(state, me, totals, target, random.Random(seed))
            worlds += 1
            if time.perf_counter() - started > budget:
                break

        return max(range(len(candidates)), key=lambda i: sums[i])

    def _rollout(self, state: SimState, me: int, totals: list, target: int, rng: random.Random) -> float:
        steps = 0
        limit = self.config.max_rollout_steps
        policy = heuristic if self.config.rollout_policy == "heuristic" else greedy
        while not state.ended and steps < limit:
            actions = fastsim.legal_actions(state)
            if not actions:
                break
            fastsim.apply(state, policy(state, actions))
            steps += 1
        return self._value(state, me, totals, target)

    def _value(self, state: SimState, me: int, totals: list, target: int) -> float:
        value = 0.0
        if state.ended:
            for seat, hand in enumerate(state.hands):
                if seat == state.winner:
                    continue
                points = sum(CARD_POINTS[card] for card in hand)
                sign = -1.0 if seat == me else 1.0
                value += sign * points
                if totals[seat] + points >= target:
                    value += sign * self.config.elimination_value
            return value
        # Unfinished rollout: compare the points still in hand.
        for seat, hand in enumerate(state.hands):
            sign = -1.0 if seat == me else 1.0
            value -= sign * 0.5 * sum(CARD_POINTS[card] for card in hand)
        return value


def _sample_world(view, knowledge: KnowledgeEngine, me: int, rng: random.Random, infer: bool = False) -> SimState | None:
    """A full round state consistent with what we observed."""
    table = view.table
    our_hand = [fastsim.card_id(card) for card in view.you.hand]

    if len(knowledge.pile) == table.played_pile_size:
        pile = [_domain_id(card) if card is not None else None for card in knowledge.pile]
    else:
        recent = [fastsim.card_id(card) for card in table.recent_cards]
        pile = [None] * (table.played_pile_size - len(recent)) + recent

    # Bank order known after a refill, and opponent cards drawn from it.
    bank_order = None
    if knowledge.bank_order is not None and len(knowledge.bank_order) == table.bank_size:
        bank_order = [_domain_id(card) if card is not None else None for card in knowledge.bank_order]
    opponent_known = [_domain_id(card) for card in knowledge.opponent_known]

    excluded = set(our_hand)
    excluded.update(card for card in pile if card is not None)
    if bank_order is not None:
        excluded.update(card for card in bank_order if card is not None)
    excluded.update(opponent_known)
    unknown = [card for card in range(32) if card not in excluded]
    rng.shuffle(unknown)

    opponent_size = view.opponents[0].hand_size
    missing = opponent_size - len(opponent_known)
    if missing < 0:
        opponent_known, missing = [], opponent_size
    opponent_hand = None
    if infer and knowledge.opponent_excluded and missing > 0:
        # Cards the opponent held when it could not play avoid the excluded
        # set; only its `free` cards drawn since then may be anything.
        excluded_ids = {_domain_id(card) for card in knowledge.opponent_excluded}
        free = min(knowledge.opponent_free, missing)
        allowed = [card for card in unknown if card not in excluded_ids]
        if len(allowed) >= missing - free:
            constrained = allowed[: missing - free]
            others = [card for card in unknown if card not in constrained]
            opponent_hand = opponent_known + constrained + others[:free]
            rest = others[free:]
    if opponent_hand is None:
        opponent_hand = opponent_known + unknown[:missing]
        rest = unknown[missing:]
    for position, card in enumerate(pile):
        if card is None:
            if not rest:
                return None
            pile[position] = rest.pop()
    if bank_order is not None:
        for position, card in enumerate(bank_order):
            if card is None:
                if not rest:
                    return None
                bank_order[position] = rest.pop()
        rest = bank_order + rest  # leftovers only if the engine duplicated cards

    hands = [None, None]
    hands[me] = our_hand
    hands[1 - me] = opponent_hand
    drawn = [False, False]
    chaining = [False, False]
    drawn[me] = view.you.has_drawn_this_turn
    chaining[me] = view.you.is_chaining
    return SimState(
        hands=hands,
        current=me,
        top=pile[-1] if pile else NO_CARD,
        required=fastsim.SUITS.index(table.required_suit) if table.required_suit is not None else NO_SUIT,
        choose=table.must_choose_suit,
        ace=table.ace_effect_active,
        skip=view.turn.next_player_id == view.you.player_id,
        bank=rest,
        pile=pile,
        last_count=table.last_play_count,
        drawn=drawn,
        chaining=chaining,
    )


def _domain_id(card) -> int:
    """Domain card (cards.Card) -> fastsim id."""
    return fastsim.SUITS.index(fastsim.Suit[card.suit.name]) * 8 + fastsim.RANKS.index(fastsim.Rank[card.rank.name])


def heuristic(state: SimState, actions: list) -> tuple:
    """Rollout policy close to the V2.1 / public medium heuristics, for both
    players: single-card scores keep only the terms that differ between plays."""
    hand = state.hands[state.current]
    size = len(hand)
    opponent = len(state.hands[1 - state.current])
    counts = [0, 0, 0, 0]
    for card in hand:
        counts[card // 8] += 1

    suits = [action for action in actions if action[0] == SUIT]
    if suits:
        seen = [0, 0, 0, 0]
        for card in state.pile[-3:]:
            seen[card // 8] += 1

        def suit_score(action) -> float:
            suit = action[1]
            score = counts[suit] * 3 + seen[suit] * 1.2
            if counts[suit] + seen[suit] >= 7:
                score += 2
            if counts[suit] == 0:
                score -= 8
            return score

        return max(suits, key=suit_score)

    best, best_score = None, None
    for action in actions:
        if action[0] != PLAY:
            continue
        card = action[1]
        rank = card % 8
        remaining = size - 1
        if remaining == 0 and rank == QUEEN:
            score = -10_000.0
        else:
            score = float(CARD_POINTS[card])
            if remaining == 0:
                score += 2_000
            if rank == QUEEN:
                score += 55 if opponent <= 2 else 35 if opponent <= 4 else 8
            elif rank == EIGHT:
                if opponent <= 3 or remaining <= 2:
                    score += 40
                elif size >= 7:
                    score -= 45
                elif size >= 5:
                    score -= 25
                else:
                    score += 5
            elif rank == ACE:
                if state.ace:
                    score -= 12
                elif _ace_is_tactical(state, counts):
                    score += 18
                elif opponent <= 3:
                    score += 10
            if remaining == 1:
                for other in hand:
                    if other != card and other % 8 == QUEEN:
                        score -= 40
        if best_score is None or score > best_score:
            best, best_score = action, score
    if best is not None:
        return best

    for action in actions:
        if action[0] == PASS:
            return action
    return actions[0]


def _ace_is_tactical(state: SimState, counts: list) -> bool:
    if state.required != NO_SUIT:
        return counts[state.required] == 0
    top = state.top
    if top == NO_CARD:
        return False
    if top % 8 == ACE:
        return True
    return counts[top // 8] == 0


def greedy(state: SimState, actions: list) -> tuple:
    """Fast rollout policy for both players."""
    hand = state.hands[state.current]

    if state.choose and any(action[0] == SUIT for action in actions):
        counts = [0, 0, 0, 0]
        for card in hand:
            counts[card // 8] += 1
        best_suit = max(range(4), key=lambda suit: counts[suit])
        for action in actions:
            if action[0] == PLAY and action[1] % 8 == EIGHT:
                continue
            if action == (SUIT, best_suit):
                return action

    best, best_score = None, None
    size = len(hand)
    top = state.top
    for action in actions:
        if action[0] != PLAY:
            continue
        card = action[1]
        rank = card % 8
        score = CARD_POINTS[card]
        if rank == EIGHT:
            score += -40 if size > 3 else 40
        elif rank == QUEEN:
            score += -1000 if size == 1 else 15
        elif rank == ACE:
            score += 5
        if top != NO_CARD and top % 8 == rank:
            for other in hand:
                if other != card and other % 8 == rank:
                    score += 12
        if best_score is None or score > best_score:
            best, best_score = action, score
    if best is not None:
        return best

    for action in actions:
        if action[0] == PASS:
            return action
    return actions[0]
