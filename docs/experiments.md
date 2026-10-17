# Expériences et benchmarks

Environnement : `i151-arena-sdk 0.2.10`, `i151-engine 0.2.4`, Windows, mode
local non isolé.

## Protocole

### Ne pas utiliser de seeds consécutifs

La donne de la manche `r` d'un match de seed `s` est tirée avec
`Random(s + r)` (`i151_engine/game/round.py`). Les seeds `s` et `s + 1`
partagent donc presque toutes leurs donnes, décalées d'une manche.

`--seed 42 --games 100` (seeds 42..141) ne contient qu'environ 130 donnes
distinctes, et chevauche `--seed 123`. Contrôle : sur le panel corrélé
10000..10499, `medium` contre lui-même ne gagne que 40–42 % ; sur un panel
aléatoire, 49,9 %.

Les résultats antérieurs obtenus avec les seeds 42 et 123 ne sont donc pas
exploitables.

### Commande de référence

```powershell
arena match bot.py --vs medium --games 1000 --seed <panel> --random --starter p0 --decision-timeout-ms 400 --format json
arena match bot.py --vs medium --games 1000 --seed <panel> --random --starter p1 --decision-timeout-ms 400 --format json
```

- `--random --seed X` : panel reproductible de seeds tirés dans [0, 2e9].
- `--starter p0` puis `p1` : chaque seed est joué avec chaque premier joueur.
- `--decision-timeout-ms 400` : limite du règlement.
- Comparaison **appariée** par (seed, premier joueur) ; IC95 sur la
  différence des victoires.
- Panels : `2026` = développement, `777` = confirmation (jamais utilisé
  pour régler un paramètre).

### Timeouts locaux

En mode non isolé, le CLI joue tous les matchs dans un seul processus. Le
tas grossit et des collectes GC de génération 2 atteignent 2,3 s. La pause
est imputée à la décision en cours, donc au bot qui alloue le plus. Ces
timeouts ne se reproduisent pas quand on rejoue le seed seul. Le temps de
décision réel de V2.3 : médiane 0,02 ms, p99,9 0,76 ms, maximum 17,6 ms sur
115 000 décisions.

`--isolated` (le mode de la compétition) échoue sous Windows
(`select()` sur des pipes, `WinError 10093`).

## Règles vérifiées dans le moteur

- `legal_actions` ne génère jamais `PLAY_MULTIPLE_CARDS` : chaque action
  joue une seule carte.
- Un tour peut contenir plusieurs cartes : enchaînement d'un même rang
  (si le rang joué égale celui du dessus et qu'il en reste en main), ou Dame
  en duel (l'adversaire est sauté).
- Sur un As, seuls un As ou un 8 peuvent être joués, même après la pioche
  de pénalité.
- Le perdant d'une manche ajoute les points de sa main. Trois manches
  gagnées d'affilée valent -10. Un joueur est éliminé à `>= 151`.

## Résultats

### Baseline contre `medium` (panel 2026, 2000 parties)

| Bot | Victoires | IC95 |
| --- | --------: | ---: |
| V1 (`archive/bots/bot_v1.py`) | 29,5 % | ±2,0 |
| V2 | 49,2 % | ±2,2 |
| V2.1 | 50,1 % | ±2,2 |
| `medium` (miroir) | 49,9 % | ±2,2 |

- V2 et V2.2 donnent exactement les mêmes parties : dans V2,
  `Counter(cards)[suit]` vaut toujours 0, donc les termes supprimés par V2.2
  étaient déjà inactifs.
- V2.1 − V2 : +0,9 ± 1,8 point, non significatif.
- V2/V2.1 reprennent les poids de `public_examples/medium_bot`, d'où la
  parité.

### V2.3 : valeur de continuation (retenue)

**Problème.** Les termes de V2 liés au nombre de cartes jouées sont constants,
puisque chaque action ne joue qu'une carte. Le bot ne voit pas qu'un coup
permet d'en jouer d'autres dans le même tour. Dans `replay-v2.json`, 12
décisions sur 126 ont joué une carte sans suite alors qu'une suite était
légale.

**Modification.** Un coup est noté par la meilleure séquence qu'il ouvre dans
le tour (enchaînement de même rang, Dame en duel), avec la fonction de score
existante. Le 8 termine la séquence. Aucun autre paramètre n'est modifié.

| Panel | V2.3 | V2.1 | Différence appariée |
| ----- | ---: | ---: | ------------------: |
| `medium`, 2026 (dev) | 54,2 % | 50,1 % | +4,1 ± 2,1 |
| `medium`, 777 (confirmation) | 59,7 % | 54,1 % | +5,6 ± 2,0 |
| `basic`, 2026 | 81,8 % | 77,9 % | +3,9 ± 1,7 |

Les 6 timeouts de V2.3 (sur 6000 parties) sont comptés comme des défaites.
Ils relèvent de l'artefact GC décrit plus haut.

**Décision.** V2.3 devient `bot.py`.

## Pistes non testées

- Enchaînement de plusieurs 8 dans la séquence.
- Verrou de l'As (seuls As/8 jouables) non modélisé.
- Choix de couleur : uniquement le nombre de cartes en main.
- Aucune mémoire des cartes jouées pendant la manche.
