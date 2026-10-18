
"""Master-i151 V2.3 — V2.1 + valeur de continuation dans le tour.

Seul écart avec V2.1 : un coup est évalué par la meilleure séquence
(enchaînement de même rang, dame en duel) qu'il permet dans le même tour.

Principes :
- Ne choisir que parmi les actions légales du moteur.
- Évaluer une action complète, pas seulement une carte.
- Privilégier la réduction du nombre de cartes en main.
- Adapter l'utilisation du huit à la situation.
- Utiliser la dame pour ralentir l'adversaire.
- Choisir une couleur qui nous laisse des possibilités.
"""

from collections import Counter

from arena_sdk import ActionType
from i151_engine.models.card import Rank, Suit


def _is_type(action, action_type):
    """Vérifie le type d'une action avec l'enum officiel."""
    return action.type == action_type


def _action_cards(action):
    """Renvoie les cartes jouées par une action, dans leur ordre."""
    if _is_type(action, ActionType.PLAY_CARD):
        return (action.card,) if action.card is not None else ()

    if _is_type(action, ActionType.PLAY_MULTIPLE_CARDS):
        return tuple(action.cards or ())

    return ()


def _opponent(view):
    """Récupère l'adversaire, si sa présence est connue."""
    if view.opponents:
        return view.opponents[0]
    return None


def _remaining_hand(view, played_cards):
    """Calcule notre main après une action, sans modifier l'état réel."""
    remaining = list(view.you.hand)

    for card in played_cards:
        if card in remaining:
            remaining.remove(card)

    return remaining


def _finishes_on_queen(view, cards):
    """En duel, évite de terminer la manche avec une dame."""
    return (
        view.match.player_count == 2
        and len(cards) == view.you.hand_size
        and bool(cards)
        and cards[-1].rank == Rank.QUEEN
    )


def _ace_is_tactical(view):
    """Estime si jouer un as peut gêner le prochain joueur."""
    if view.table.ace_effect_active:
        return False

    hand_counts = Counter(card.suit for card in view.you.hand)
    required_suit = view.table.required_suit

    if required_suit is not None:
        return hand_counts[required_suit] == 0

    top_card = view.table.top_card

    if top_card is None:
        return False

    if top_card.rank == Rank.ACE:
        return True

    return hand_counts[top_card.suit] == 0


def _card_context(view, card, remaining_count):
    """Évalue l'intérêt tactique d'une carte particulière."""
    opponent = _opponent(view)
    opponent_count = opponent.hand_size if opponent else 99

    bonus = 0.0

    # Le huit vaut 32 points : le jouer trop tôt peut être inutile.
    if card.rank == Rank.EIGHT:
        if opponent_count <= 3 or remaining_count <= 2:
            bonus += 40
        elif view.you.hand_size >= 7:
            bonus -= 45
        elif view.you.hand_size >= 5:
            bonus -= 25
        else:
            bonus += 5

    # L'as peut être utile selon l'effet actif et la couleur requise.
    if card.rank == Rank.ACE:
        if view.table.ace_effect_active:
            bonus -= 12
        elif _ace_is_tactical(view):
            bonus += 18
        elif opponent_count <= 3:
            bonus += 10

    return bonus


def _continuations(view, first):
    """Énumère les suites jouables dans le même tour après ``first``.

    Le moteur ne propose que des coups d'une carte ; un tour peut pourtant
    en contenir plusieurs (règles lues dans i151_engine.core.reducer) :
    - enchaînement : le rang joué égale celui du dessus et il en reste en main ;
    - dame en duel : l'adversaire est sauté, on rejoue sur la dame.
    Un 8 termine la séquence (choix de couleur ; enchaînement de 8 ignoré).
    """
    duel = view.match.active_player_count == 2
    sequences = []

    def explore(hand, top, played):
        sequences.append(tuple(played))
        card = played[-1]

        if not hand or card.rank == Rank.EIGHT:
            return

        same_rank = [c for c in hand if c.rank == card.rank]

        if top is not None and top.rank == card.rank and same_rank:
            nexts = same_rank
        elif card.rank == Rank.QUEEN and duel:
            nexts = [c for c in hand if c.can_play_on_with_required_suit(card, None)]
        else:
            return

        for nxt in nexts:
            rest = list(hand)
            rest.remove(nxt)
            explore(rest, card, played + [nxt])

    hand = list(view.you.hand)
    if first in hand:
        hand.remove(first)
    explore(hand, view.table.top_card, [first])

    return sequences


def _score_action(view, action):
    """Score d'un coup = meilleure séquence qu'il ouvre dans le même tour."""
    cards = _action_cards(action)

    if len(cards) != 1:
        return _score_cards(view, cards)

    return max(
        _score_cards(view, sequence)
        for sequence in _continuations(view, cards[0])
    )


def _score_cards(view, cards):
    """Attribue un score tactique à une séquence de cartes jouées."""
    if not cards:
        return float("-inf")

    # En duel, finir sur une dame est considéré comme risqué.
    if _finishes_on_queen(view, cards):
        return -10_000

    opponent = _opponent(view)
    opponent_count = opponent.hand_size if opponent else 99

    played_count = len(cards)
    remaining_count = view.you.hand_size - played_count
    dumped_points = sum(card.points for card in cards)

    # Score de base : vider des cartes compte plus que leur valeur seule.
    score = played_count * 28
    score += dumped_points
    score -= remaining_count * 6

    # Vider sa main remporte normalement la manche.
    if remaining_count == 0:
        score += 2_000

    # Si l'adversaire approche de la fin, accélérer devient prioritaire.
    if opponent_count <= 3:
        score += played_count * 18
        score -= remaining_count * 10

    if view.you.hand_size <= 4:
        score += played_count * 12

    # En duel, la dame peut faire perdre un tour à l'adversaire.
    if (
        cards[-1].rank == Rank.QUEEN
        and view.match.player_count == 2
        and remaining_count > 0
    ):
        if opponent_count <= 2:
            score += 55
        elif opponent_count <= 4:
            score += 35
        else:
            score += 8

    # Bonus et pénalités selon les cartes de l'action.
    for card in cards:
        score += _card_context(view, card, remaining_count)

    # Éviter de garder uniquement une dame en fin de main à deux joueurs.
    if remaining_count == 1 and view.match.player_count == 2:
        remaining_hand = _remaining_hand(view, cards)

        if (
            len(remaining_hand) == 1
            and remaining_hand[0].rank == Rank.QUEEN
        ):
            score -= 40

    return score


def _seen_table_cards(view):
    """Récupère les cartes visibles dans les informations de table."""
    seen = list(view.table.recent_cards)

    for card in view.table.last_play_cards:
        if card not in seen:
            seen.append(card)

    return seen


def _choose_suit(view, actions):
    """Choisit une couleur qui conserve des options pour les prochains tours."""
    hand_counts = Counter(card.suit for card in view.you.hand)
    table_counts = Counter(
        card.suit for card in _seen_table_cards(view)
    )

    def suit_score(action):
        suit = action.chosen_suit

        if suit is None:
            return float("-inf")

        score = hand_counts[suit] * 3
        score += table_counts[suit] * 1.2

        # Une couleur presque épuisée peut être intéressante à imposer.
        if hand_counts[suit] + table_counts[suit] >= 7:
            score += 2

        # Éviter de choisir une couleur que nous n'avons pas en main.
        if hand_counts[suit] == 0:
            score -= 8

        return score

    return max(actions, key=suit_score)


def decide(view, legal_actions, time_left_ms):
    """Point d'entrée attendu par le moteur du challenge."""
    del time_left_ms

    if not legal_actions:
        raise ValueError("Le moteur n'a fourni aucune action légale.")

    # 1. Traiter en priorité un éventuel choix de couleur.
    suit_actions = [
        action
        for action in legal_actions
        if _is_type(action, ActionType.CHOOSE_SUIT)
    ]

    if suit_actions:
        return _choose_suit(view, suit_actions)

    # 2. Comparer toutes les actions qui jouent des cartes.
    play_actions = [
        action
        for action in legal_actions
        if action.type in (
            ActionType.PLAY_CARD,
            ActionType.PLAY_MULTIPLE_CARDS,
        )
    ]

    if play_actions:
        return max(play_actions, key=lambda action: _score_action(view, action))

    # 3. Si passer est légal, préférer cette option à une pioche.
    for action in legal_actions:
        if _is_type(action, ActionType.PASS_TURN):
            return action

    # 4. Sinon, laisser le moteur décider parmi les options légales restantes.
    return legal_actions[0]
