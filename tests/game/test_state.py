"""arena_adapter.to_game_state on real engine views."""

from __future__ import annotations

from i151_engine.game.round import create_match
from i151_engine.view.builder import build_player_view

from arena_adapter import to_card, to_game_state


def _view(seed: int = 3, player: str = "p0"):
    match = create_match(("A", "B"), seed=seed)
    return build_player_view(match, match.current_round, player, opponent_specs={}, step_index=0)


def test_state_copies_public_information_only():
    view = _view()
    state = to_game_state(view)

    assert state.you.hand == [to_card(card) for card in view.you.hand]
    assert state.you.hand_size == len(view.you.hand) == 8
    assert state.opponent.hand_size == view.opponents[0].hand_size == 8
    assert state.opponent.hand == []
    assert state.player_count == state.active_player_count == 2
    assert state.round_number == 1
    assert state.target_score == 151
    assert state.table.top_card is None
    assert state.table.played_pile_size == 0
