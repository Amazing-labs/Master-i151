
"""Premier bot fonctionnel pour le challenge i151.

Principe :
- choisir uniquement parmi les actions légales fournies par le moteur ;
- privilégier les cartes qui réduisent fortement les points de la main ;
- choisir une couleur en fonction des cartes restantes ;
- toujours disposer d'une action de secours légale.
"""


def _action_type(action) -> str:
    """Retourne la valeur textuelle du type d'action."""
    return getattr(action.type, "value", str(action.type))


def _suit_card_count(hand, suit) -> int:
    """Compte les cartes d'une couleur dans notre main."""
    return sum(1 for card in hand if card.suit == suit)


def _choose_suit_action(actions, hand):
    """Choisit la couleur pour laquelle nous avons le plus de cartes."""
    suit_actions = [
        action
        for action in actions
        if _action_type(action) == "chooseSuit"
    ]

    if not suit_actions:
        return None

    return max(
        suit_actions,
        key=lambda action: _suit_card_count(
            hand,
            action.chosen_suit,
        ),
    )


def _card_priority(card, hand) -> float:
    """Estime l'intérêt immédiat de jouer une carte."""
    # Un huit vaut 32 points : le conserver en main coûte cher.
    if card.rank.name == "EIGHT":
        return 100.0

    # Les cartes à forte valeur pénalisent davantage en fin de manche.
    priority = float(card.points)

    # Conserver des cartes de la même couleur peut offrir
    # davantage de possibilités lors des prochains tours.
    same_suit_count = _suit_card_count(hand, card.suit)
    priority -= same_suit_count * 0.5

    return priority


def decide(view, legal_actions, time_left_ms):
    """Retourne une action présente dans legal_actions."""
    if not legal_actions:
        raise ValueError("Le moteur n'a fourni aucune action légale.")

    hand = view.you.hand

    # 1. Si le moteur attend un choix de couleur, le traiter d'abord.
    suit_action = _choose_suit_action(legal_actions, hand)
    if suit_action is not None:
        return suit_action

    # 2. Récupérer les actions qui jouent une ou plusieurs cartes.
    play_actions = [
        action
        for action in legal_actions
        if _action_type(action) in (
            "playCard",
            "playMultipleCards",
        )
    ]

    if play_actions:
        def action_priority(action):
            if _action_type(action) == "playCard":
                cards = (action.card,) if action.card is not None else ()
            else:
                cards = action.cards

            return sum(
                _card_priority(card, hand)
                for card in cards
            )

        return max(play_actions, key=action_priority)

    # 3. Aucune carte jouable : suivre les options légales du moteur.
    # On passe si possible après avoir pioché ; sinon on pioche.
    for preferred_type in ("passTurn", "drawCard"):
        for action in legal_actions:
            if _action_type(action) == preferred_type:
                return action

    # 4. Secours : ne jamais fabriquer une action qui pourrait être illégale.
    return legal_actions[0]
