# Règles i151 — état des connaissances (Kanté)

Convention de confiance : `RULE` (écrit dans le règlement officiel) ·
`FACT` (observé/mesuré de façon fiable dans le SDK/moteur) ·
`HYPOTHESIS` (pattern vu, pas encore confirmé) · `UNKNOWN` (ne pas s'appuyer dessus).

Source du règlement : *Règlement — Compétition IA i151, v1, 9 juillet 2026*.

## 1. Format technique (RULE — règlement §3)

| Point | Détail |
|---|---|
| Langage | Python 3.11+ uniquement |
| SDK | `pip install i151-arena-sdk` (embarque `i151_engine`) |
| Interface | `decide(view, legal_actions, time_left_ms)` dans `bot.py` |
| Temps par décision | **400 ms max** — dépassement = forfait |
| Coups par manche | 3000 max |
| Durée max partie | 10 min |
| `setup(submission_dir)` | optionnel, appelé une fois avant le match |

Conséquence pour notre module : `validators.ensure_legal()` doit rester
**rapide** (O(n) sur `legal_actions`, pas de recherche coûteuse) — c'est le
cas actuellement (comparaisons directes de dataclasses).

## 2. Interdits sandbox (RULE — règlement §3)

Accès réseau, entraînement pendant un match, lecture de la main adverse ou
de l'état moteur brut, dépendances hors whitelist, `eval`/`exec`/
`pickle.load`/`torch.load(weights_only=False)`, `asyncio`/`ssl`/`socket`,
lecture hors du dossier de soumission.

Conséquence : notre module `rules/` ne doit dépendre que de
`i151_engine` / `arena_sdk` (whitelist SDK) — aucune I/O, aucun réseau.
Vérifié : `rules.py`, `actions.py`, `validators.py` n'importent que
`i151_engine.models.*` et la stdlib (`enum`, `__future__`).

## 3. Verdict de match (RULE — règlement §3)

> Décision illégale, timeout ou crash → forfait (défaite automatique).

C'est la justification directe de `validators.ensure_legal()` : mieux
vaut lever une `ActionValidationError` détectable en test qu'un forfait
en compétition.

## 4. Types d'actions (FACT — lu dans `i151_engine.models.action`)

`ActionType` = `PLAY_CARD`, `PLAY_MULTIPLE_CARDS`, `DRAW_CARD`,
`PASS_TURN`, `CHOOSE_SUIT`. Contrat de la dataclass `Action` :
`type`, `card`, `cards`, `chosen_suit`.

## 5. Zone confirmée par simulation (FACT — mesuré, pas dans le règlement)

`PLAY_MULTIPLE_CARDS` existe dans le contrat `ActionType`/`Action`, mais
n'a **jamais** été produit par `legal_actions()` sur **2000 parties
aléatoires complètes** simulées avec le moteur publié (`i151_engine`
0.2.4, ~1 000 000 actions légales observées au total — voir
`tests/rules/test_engine_integration.py::test_zone_inconnue_play_multiple_cards_jamais_observe`).

→ Reclassé `HYPOTHESIS` → `FACT`. Ce n'est pas une `RULE` (rien d'écrit
noir sur blanc côté règlement ou doc SDK) : si une future version du
moteur change ça, le test d'intégration ci-dessus casse et nous alerte.

## 6. Règle des 8 (FACT — lu dans `i151_engine.models.card.Card`)

Une carte de rang 8 peut toujours être jouée, quelle que soit la carte du
dessus ou la couleur imposée (`Card.can_play_on_with_required_suit`).
Jouer un 8 peut être suivi d'une phase où seules des actions
`CHOOSE_SUIT` (une par couleur) sont légales.

## 7. Ce qui reste `UNKNOWN` / à surveiller

- Le détail exact du calcul des points (`hand_points`) et du score de
  manche n'a pas été audité ligne à ligne côté `core/scoring.py` — à
  documenter si Maiga ou Diarra en ont besoin pour l'évaluation.
- Le comportement exact de l'effet As multi-pioche (`draw_count_if_draw`)
  au-delà de "l'action reste un simple DRAW_CARD" n'a pas été
  approfondi ici : ça relève plutôt de `game/state.py` (Dioman).

## Où vérifier soi-même

```bash
pip install i151-arena-sdk i151-engine
python -m pytest tests/rules/ -v          # unitaires (rapides)
python -m pytest tests/rules/ -m integration -v   # contre le vrai moteur
```
