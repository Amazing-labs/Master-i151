# Master-i151 — Briefing complet pour l'agent IA

## 1. Mission

Tu interviens sur **Master-i151**, un bot Python développé pour le challenge i151 Arena organisé sur `challenge.jeu-151.com`.

Ta mission est de contribuer à terminer un bot compétitif, fiable, conforme aux règles officielles et suffisamment performant pour affronter les adversaires du challenge.

Tu ne dois pas simplement produire du code qui fonctionne. Tu dois comprendre le moteur, analyser la stratégie actuelle, identifier les faiblesses mesurables et apporter des améliorations dont la valeur est démontrée par des tests reproductibles.

Le propriétaire du projet est un développeur expérimenté qui comprend les concepts de programmation et d'architecture logicielle. Ne lui explique pas les bases inutilement et ne lui fais pas exécuter des commandes sans objectif clair.

**Résultat recherché : un bot solide, testé et compétitif, pas une collection de versions expérimentales.**

---

## 2. Contexte du projet

- Nom du projet : `Master-i151`
- Organisation GitHub : `Amazing-Labs/Master-i151`
- Langage du bot : Python
- SDK Arena installé : `i151-arena-sdk 0.2.10`
- Moteur installé : `i151-engine 0.2.4`
- Environnement de développement : Windows, PowerShell, environnement virtuel Python
- Commande de validation : `arena test bot.py`
- Commande de benchmark : `arena match`
- Objectif initial : implémenter un bot déterministe ou fondé sur des heuristiques explicites, sans entraîner ni intégrer de modèle de machine learning.

Le projet est réalisé dans le cadre d'un travail d'équipe de quatre personnes : Dioman Keïta, Kanté, Maïga et Diarra.

Les responsabilités envisagées étaient :

- Dioman : état du jeu, connaissance et informations observables.
- Kanté : règles et actions.
- Maïga : stratégie et évaluation.
- Diarra : simulation et analyse des résultats.

Ces répartitions sont le contexte initial. Vérifie le code et l'état actuel du dépôt avant de supposer que chaque responsabilité est déjà correctement implémentée.

---

## 3. Contraintes non négociables

### 3.1 Respecter le moteur officiel

Le moteur et le SDK officiels font autorité pour les règles du jeu.

Tu dois examiner les implémentations réellement installées et les documents officiels disponibles avant de modifier la stratégie.

Ne reconstitue pas les règles à partir de souvenirs ou de suppositions si le moteur permet de les vérifier.

### 3.2 Respecter l'environnement d'exécution

Le bot doit fonctionner dans l'environnement imposé par Arena.

Les modules `arena_sdk` et `i151_engine` sont fournis par le sandbox et ne doivent pas être ajoutés artificiellement aux dépendances du bot.

Les contraintes de sécurité et de soumission précédemment communiquées comprennent notamment :

- Pas de réseau.
- Pas de communication externe.
- Pas de processus système lancés par le bot.
- Pas de chargement dynamique de modèles.
- Pas de dépendance à un service externe.
- Pas d'apprentissage automatique nécessaire au fonctionnement.
- Utilisation limitée aux bibliothèques autorisées par le règlement du challenge.

Les exemples de modules standards autorisés précédemment identifiés comprennent `math`, `random`, `itertools`, `collections`, `json` et `typing`.

Les modules `os`, `socket`, `ssl`, `asyncio`, `subprocess`, `pickle`, `http`, `urllib` et `multiprocessing` ont été cités comme exemples interdits dans les consignes précédemment examinées.

**Vérifie la liste officielle complète avant la soumission.** Ne considère pas cette liste indicative comme une copie exhaustive du règlement.

### 3.3 Ne jamais fabriquer une action

Le moteur fournit les actions légales disponibles.

Le bot doit choisir une action parmi celles-ci, sans créer artificiellement une action qui pourrait être refusée.

### 3.4 Respecter les informations réellement disponibles

Le bot ne connaît pas les cartes cachées des adversaires.

Il est interdit de fonder une décision opérationnelle sur les cartes adverses révélées uniquement dans un replay rétrospectif.

Les replays peuvent servir à analyser les parties terminées, mais pas à donner au bot des informations qu'il ne possédait pas au moment de jouer.

---

## 4. Compréhension du jeu

Les informations suivantes ont été relevées pendant le développement. Elles doivent être vérifiées dans les règles officielles et le moteur avant toute décision stratégique importante.

### 4.1 Cartes et points

Le jeu utilise les rangs suivants :

- 7
- 8
- 9
- 10
- Valet
- Dame
- Roi
- As

Les quatre couleurs sont celles définies par le moteur.

Les valeurs de points identifiées sont :

| Carte | Points |
| ----- | -----: |
| 7     |      7 |
| 8     |     32 |
| 9     |      9 |
| 10    |     10 |
| Valet |      2 |
| Dame  |      3 |
| Roi   |      4 |
| As    |     11 |

Vérifie la construction du paquet, le nombre de cartes, les règles de distribution et les éventuelles particularités des cartes.

### 4.2 Structure de la partie

Le modèle de travail adopté est le suivant :

- Une partie complète contient plusieurs manches.
- Les joueurs effectuent leurs actions à tour de rôle.
- Les scores évoluent entre les manches.
- Une partie se termine lorsqu'un joueur atteint le seuil d'élimination.

Le seuil de 151 points a été identifié comme déterminant.

Les éléments suivants doivent être confirmés à partir du moteur :

- La définition exacte d'une manche gagnée.
- Le calcul du score de manche.
- La pénalité appliquée au joueur qui perd une manche.
- La signification de `hand_points`, `hand_score` et `total_score`.
- Le fonctionnement du bonus de trois manches consécutives gagnées, identifié comme une pénalité de -10 points.
- Le comportement exact lorsque le seuil de 151 points est atteint.
- Les conditions de fin exceptionnelles, les limites de durée et les limites de coups éventuelles.
- Le rôle de l'Elo et des résultats de match dans le classement du challenge.

Ne code aucune de ces règles à partir de cette description seule si la source officielle peut les confirmer.

### 4.3 Actions et règles spéciales

Les actions identifiées dans le SDK comprennent :

- Jouer une carte.
- Jouer plusieurs cartes.
- Piocher.
- Passer son tour.
- Choisir une couleur.

Les observations antérieures indiquent que :

- Les coups doivent respecter les contraintes de rang et de jeu en cours.
- Le 8 possède une règle spéciale permettant de le jouer indépendamment de la couleur ou de la contrainte habituelle.
- Jouer un 8 implique un choix de couleur.
- Les actions multiples peuvent concerner de 1 à 8 cartes selon les règles et les conditions légales.
- Certaines règles concernant les Dames ont été identifiées pour les parties à deux joueurs.

Ces points doivent être vérifiés dans les sources installées et les règles officielles, notamment pour les interactions entre enchaînement, jeu multiple, pioche et passage.

---

## 5. API du bot

Le contrat identifié pour le bot est :

```python
def decide(view, legal_actions, time_left_ms):
    ...
```

Le bot doit retourner une action valide parmi `legal_actions`.

Les types SDK inspectés comprennent notamment :

- `PlayerView`
- `Action`
- `ActionType`

Le `PlayerView` expose les groupes d'informations suivants :

- `view.you`
- `view.opponents`
- `view.table`
- `view.turn`
- `view.match`

L'état du joueur contient notamment des informations telles que :

- `hand`
- `hand_size`
- `hand_points`
- `total_score`
- `is_excluded`
- `has_drawn_this_turn`
- `is_chaining`
- `consecutive_round_wins`

Les états des adversaires exposent des informations limitées, dont leur taille de main et leur score, sans révéler leurs cartes cachées.

Les informations de table comprennent notamment des cartes récentes et les dernières cartes jouées, selon la version du SDK.

Les noms précis, les valeurs des énumérations, les champs optionnels et les conditions d'utilisation doivent être vérifiés dans la version installée.

**Ne suppose jamais qu'un champ existe ou qu'il a une signification donnée sans examiner sa définition.**

---

## 6. Historique des versions et résultats mesurés

Plusieurs versions ont été évaluées. Les résultats ne doivent pas être interprétés comme une preuve de supériorité générale sur la base de quelques graines.

### 6.1 Bot de référence : `bot.py` (V1)

La V1 est un bot fonctionnel simple qui :

- Utilise les actions légales fournies par le moteur.
- Privilégie les cartes à forte valeur de points.
- Accorde une forte priorité au 8.
- Évalue le choix de couleur à partir des cartes conservées en main.
- Possède une action de secours si aucun cas stratégique n'est traité.

Résultats précédemment obtenus :

| Adversaire | Seed | Matchs | Victoires |
| ---------- | ---: | -----: | --------: |
| `random`   |   42 |    100 |     100 % |
| `basic`    |   42 |    100 |      70 % |
| `medium`   |   42 |    100 |      22 % |
| `medium`   |  123 |    100 |      53 % |

Le résultat de 22 % contre `medium` avec le seed 42 a également été obtenu avec un paramètre de premier joueur fixé à 50 %.

La V1 est une référence historique, pas nécessairement la meilleure stratégie possible.

### 6.2 Bot `bot_v2.py` (V2)

La V2 a introduit une évaluation plus élaborée :

- Nombre de cartes jouées.
- Points retirés de la main.
- Taille de la main restante.
- Bonus pour terminer une manche.
- Traitement contextuel de certaines cartes, notamment les Dames, As et 8.
- Choix de couleur fondé sur les cartes en main et des informations récentes de table.

Résultats :

| Adversaire | Seed | Matchs | Victoires |
| ---------- | ---: | -----: | --------: |
| `basic`    |   42 |    100 |      72 % |
| `medium`   |   42 |    100 |      34 % |
| `basic`    |  123 |    100 |      50 % |
| `medium`   |  123 |    100 |      41 % |

La V2 n'a donc pas démontré une amélioration générale par rapport à la V1.

### 6.3 Bot `bot_v2_1.py` (V2.1)

Une erreur de comptage dans la sélection de couleur a été identifiée.

Code initial :

```python
table_counts = Counter(_seen_table_cards(view))
```

Ce code compte les objets carte entiers. Or, la suite de la fonction interroge le compteur avec une couleur.

Correction :

```python
table_counts = Counter(
    card.suit for card in _seen_table_cards(view)
)
```

Résultats contre `medium` :

| Seed | Matchs |   V2 | V2.1 |
| ---- | -----: | ---: | ---: |
| 42   |    100 | 34 % | 15 % |
| 123  |    100 | 41 % | 44 % |

La correction a donc produit des effets différents selon les graines.

Attention : les informations de table utilisées dans ce calcul ne constituent pas nécessairement un historique complet des cartes jouées pendant toute la manche.

### 6.4 Bot `bot_v2_2.py` (V2.2)

Cette version a été créée à partir de V2.1 en retirant deux bonus liés aux cartes récentes :

```python
score += table_counts[suit] * 1.2
```

et :

```python
if hand_counts[suit] + table_counts[suit] >= 7:
    score += 2
```

Résultats observés :

| Seed | Matchs |   V2 | V2.1 | V2.2 |
| ---- | -----: | ---: | ---: | ---: |
| 42   |    100 | 34 % | 15 % | 34 % |
| 123  |    100 | 41 % | 44 % | 41 % |

V2.2 reproduit les taux de victoire de V2 sur ces deux graines.

Cela ne prouve pas que les deux versions choisissent les mêmes actions. Il faut comparer les décisions ou examiner le code si cette équivalence est importante.

### 6.5 Interprétation

Conclusions autorisées :

- Toutes les versions citées fonctionnent au moins dans les tests déjà réussis.
- V1 est une référence à préserver.
- V2 a montré une sensibilité importante aux graines.
- La correction du compteur a un effet stratégique non uniforme.
- Les résultats disponibles ne permettent pas de déclarer V1, V2 ou V2.1 définitivement supérieure.

Conclusions interdites :

- Affirmer qu'une version est meilleure à partir d'une seule série.
- Attribuer toute une variation de score à une ligne de code sans isoler son effet.
- Confondre égalité des taux de victoire et égalité des décisions.
- Présenter une heuristique comme améliorée uniquement parce qu'elle paraît plus logique.

---

## 7. Replay disponible

Un replay nommé `replay-v2.json` a été analysé précédemment.

Le résultat final enregistré était :

- Vainqueur : `p1`.
- Score final de `p0` : 160.
- Score final de `p1` : 99.
- Raison : `normal`.
- Nombre de manches : 27.
- V2 a remporté 12 manches et l'adversaire 15.

Ce replay montre que V2 était capable de gagner plusieurs manches, notamment au milieu de la partie, mais a ensuite perdu plusieurs manches consécutives.

Une observation a été faite sur la sélection de couleur : dans certaines situations, le bot conservait des cartes réparties entre plusieurs couleurs, ce qui pouvait rendre son choix moins déterminant.

Une autre observation concernait la fin de la partie : V2 a perdu une manche avec plusieurs cartes encore en main, dont des cartes à forte valeur de points.

Ces observations sont des pistes d'analyse, pas des preuves qu'un coup particulier était mauvais.

Si le replay est toujours disponible :

1. Identifie les décisions prises par le bot.
2. Reconstitue l'état observable à chaque décision.
3. Examine les actions légales réellement disponibles.
4. Compare l'action choisie aux alternatives légales.
5. Vérifie si l'alternative aurait amélioré la situation selon les règles et les informations disponibles à cet instant.
6. Sépare clairement l'analyse rétrospective de ce que le bot pouvait réellement savoir.

Ne donne jamais au bot accès aux cartes cachées révélées uniquement dans les snapshots de replay.

---

## 8. Architecture et modèle de connaissance

Le projet a envisagé une séparation conceptuelle entre :

- État observable du jeu.
- Connaissance des cartes.
- Règles et actions.
- Évaluation stratégique.
- Décision finale.

Le rôle initial de Dioman était notamment de travailler sur l'état du jeu et le moteur de connaissance.

L'objectif d'un tel moteur de connaissance n'est pas de prétendre connaître les cartes adverses. Il doit distinguer correctement :

1. Les cartes présentes dans notre main.
2. Les cartes visibles ou révélées.
3. Les cartes dont l'emplacement peut être déduit avec certitude, si les règles et l'historique le permettent.
4. Les cartes inconnues.
5. Les informations probabilistes ou les hypothèses, qui ne doivent jamais être confondues avec des faits.

Avant de proposer une architecture nouvelle, inspecte les modules déjà présents dans le dépôt.

Ne recrée pas un moteur de connaissance complet si le projet dispose déjà d'une implémentation exploitable. Ne multiplie pas les classes et les couches sans besoin démontré.

L'architecture doit rester proportionnée à la complexité réelle du bot et aux contraintes du sandbox.

---

## 9. Méthode de travail obligatoire

### Étape 1 — Auditer avant de modifier

Commence par examiner :

- L'arborescence du dépôt.
- `bot.py`.
- `bot_v2.py`.
- `bot_v2_1.py`.
- `bot_v2_2.py`.
- Les modules de connaissance, règles et stratégie réellement présents.
- Les tests existants.
- Le moteur et le SDK installés.
- Les consignes officielles de soumission.

Ne suppose pas que tous les fichiers cités sont encore présents ou identiques aux versions décrites ici.

Présente un diagnostic factuel : ce qui fonctionne, ce qui est incomplet, ce qui est suspect et ce qui doit être vérifié.

### Étape 2 — Établir une baseline reproductible

Avant toute modification :

- Vérifie que les versions actuelles réussissent `arena test`.
- Exécute des benchmarks sur des graines fixées.
- Conserve les résultats et les paramètres de chaque test.
- Enregistre les versions exactes du code utilisées.
- Vérifie la répartition du premier joueur.
- Vérifie que les mêmes adversaires et les mêmes paramètres sont utilisés pour comparer les versions.

Ne confonds pas une série de 100 matchs avec une mesure définitive de la force d'un bot.

### Étape 3 — Identifier un défaut concret

Chaque modification doit répondre à une question précise.

Exemples :

- Le bot conserve-t-il trop souvent des cartes qui lui coûtent beaucoup de points ?
- Choisit-il une couleur sans disposer d'assez de cartes de cette couleur ?
- Sacrifie-t-il une bonne combinaison pour un gain immédiat de points ?
- Néglige-t-il les conditions de fin de manche ?
- Gère-t-il correctement les règles de pioche, d'enchaînement et de passage ?
- Évalue-t-il mal le risque de perdre la manche avec une main coûteuse ?

Ces exemples sont des hypothèses à examiner, pas des problèmes déjà prouvés.

### Étape 4 — Modifier une seule chose à la fois

Pour chaque changement :

1. Énonce le problème.
2. Décris la cause supposée.
3. Propose la modification minimale.
4. Explique l'effet attendu.
5. Ajoute ou adapte les tests nécessaires.
6. Lance les benchmarks contrôlés.
7. Compare les résultats.
8. Conserve ou rejette la modification selon les preuves.

Ne change pas simultanément la sélection de couleur, la fonction de score, la gestion des 8 et la stratégie de fin de manche.

### Étape 5 — Utiliser des comparaisons solides

Les graines 42 et 123 sont utiles pour reproduire les résultats déjà observés, mais elles ne suffisent pas à caractériser la force générale du bot.

Utilise ensuite plusieurs graines indépendantes et un nombre de matchs suffisant pour réduire l'incertitude.

Pour comparer deux bots :

- Utilise les mêmes graines lorsque le moteur le permet.
- Contrôle la répartition du premier joueur.
- Vérifie que les distributions de départ sont comparables.
- Enregistre les résultats par graine, pas uniquement un taux global.
- Mesure aussi les forfaits, les erreurs et les durées si ces données sont disponibles.
- Calcule les incertitudes statistiques lorsque cela est pertinent.

Si le moteur permet de fixer exactement le joueur qui commence, utilise ce mécanisme pour contrôler les essais. Ne suppose pas qu'un taux configuré de 50 % produit nécessairement exactement 50 % de départs pour chaque joueur dans chaque série.

### Étape 6 — Analyser les échecs

Quand une série régresse :

- Examine les replays représentatifs.
- Identifie les décisions qui contribuent au problème.
- Sépare les erreurs de règles des erreurs stratégiques.
- Compare les alternatives réellement légales.
- Vérifie si le problème se reproduit sur plusieurs graines.
- Ne généralise pas à partir d'un seul replay.

### Étape 7 — Consolider

Une fois une amélioration validée :

- Intègre-la proprement dans la version retenue.
- Supprime ou archive les expériences devenues inutiles si cela convient à la gestion du dépôt.
- Ajoute des tests de régression pertinents.
- Vérifie la compatibilité avec le sandbox.
- Exécute le test officiel.
- Vérifie le packaging final.

Ne remplace pas automatiquement la référence stable par la dernière version expérimentale.

---

## 10. Commandes de travail connues

Dans PowerShell, avec l'environnement virtuel activé :

Validation :

```powershell
arena test bot.py
```

Benchmark contre l'adversaire aléatoire :

```powershell
arena match bot.py --vs random --games 100 --seed 42 --format summary
```

Benchmark contre `basic` :

```powershell
arena match bot.py --vs basic --games 100 --seed 42 --format summary
```

Benchmark contre `medium` :

```powershell
arena match bot.py --vs medium --games 100 --seed 42 --p0-first-rate 50% --format summary
```

Reproduire une série avec une autre graine :

```powershell
arena match bot.py --vs medium --games 100 --seed 123 --p0-first-rate 50% --format summary
```

Produire un replay pour analyser un match :

```powershell
arena match bot.py --vs medium --games 1 --seed 42 --replay-out replay.json
```

Le nom `medium` a été observé comme un alias de `medium_bot`, un adversaire d'exemple public. Il ne faut pas le confondre automatiquement avec un adversaire interne nommé `builtin:medium`.

Vérifie les commandes réellement disponibles avec :

```powershell
arena --help
arena match --help
arena test --help
```

Le CLI identifié expose les commandes principales `match`, `test`, `init` et `pack`.

---

## 11. Qualités stratégiques à viser

Le bot final devrait prendre en compte les dimensions suivantes, dans la mesure où elles sont utiles et autorisées.

### 11.1 Valeur de la main restante

Évaluer uniquement les points éliminés est insuffisant.

Le bot doit également considérer :

- Les points encore en main.
- Les possibilités de jouer aux prochains tours.
- La diversité et la distribution des couleurs.
- Les cartes difficiles à défausser.
- La capacité à terminer une manche.
- Les conséquences probables du coup sur les prochains tours.

### 11.2 Combinaisons et actions multiples

Quand plusieurs actions sont légales, évaluer le bénéfice de jouer plusieurs cartes ensemble.

La décision doit prendre en compte la valeur des cartes défaussées, la main restante et les possibilités de jeu après l'action.

Ne suppose pas que jouer le plus grand nombre de cartes est toujours optimal.

### 11.3 Cartes spéciales

Évaluer les cartes spéciales en fonction de la situation réelle du jeu.

Le 8 vaut 32 points, mais sa capacité spéciale peut également être stratégique. Le bot ne doit ni le conserver systématiquement ni le jouer systématiquement en premier.

Les règles des autres cartes spéciales doivent être confirmées dans le moteur avant d'être intégrées à l'évaluation.

### 11.4 Choix de couleur

Le choix d'une couleur devrait considérer les cartes que le bot possède réellement, les contraintes du jeu et les conséquences probables sur ses prochaines actions.

Un historique partiel de cartes récentes ne doit pas être traité comme un décompte complet des cartes restantes.

Les hypothèses sur les cartes adverses doivent être explicitement probabilistes si elles sont utilisées.

### 11.5 Fin de manche et score global

La meilleure action peut dépendre du score cumulé et des conditions exactes de victoire ou d'élimination.

La stratégie doit être évaluée à l'échelle de la manche et de la partie, pas uniquement en fonction du nombre de points retirés au tour courant.

---

## 12. Ce que l'agent ne doit pas faire

- Ne pas réécrire tout le projet avant d'avoir compris le code existant.
- Ne pas introduire de machine learning.
- Ne pas ajouter de dépendances inutiles.
- Ne pas contourner les contraintes du sandbox.
- Ne pas inventer de règles.
- Ne pas utiliser les cartes cachées des adversaires.
- Ne pas présenter une intuition comme un résultat expérimental.
- Ne pas multiplier les versions sans raison.
- Ne pas faire modifier plusieurs heuristiques à la fois.
- Ne pas lancer des centaines de matchs sans expliquer ce qu'ils doivent mesurer.
- Ne pas demander à l'utilisateur de recopier manuellement des informations déjà présentes dans le dépôt.
- Ne pas remplacer la baseline sans validation.
- Ne pas confondre une réussite de `arena test` avec une preuve de force stratégique.

Si une information essentielle manque, cherche-la dans les fichiers du projet, le SDK ou le moteur avant de poser une question à l'utilisateur.

---

## 13. Définition du travail terminé

Le bot ne sera pas considéré comme terminé simplement parce qu'il passe `arena test`.

Le travail devra démontrer :

1. **Conformité :** respect des règles officielles et des contraintes de soumission.
2. **Fiabilité :** absence de forfaits et de décisions invalides dans les essais réalisés.
3. **Compréhension :** règles importantes documentées et comportement explicable.
4. **Performance :** résultats mesurés sur plusieurs graines et plusieurs adversaires.
5. **Comparabilité :** baseline et méthode de benchmark reproductibles.
6. **Robustesse :** stratégie qui ne dépend pas d'un résultat isolé.
7. **Maintenabilité :** code raisonnablement simple, sans complexité gratuite.
8. **Soumission :** package final testé avec les outils officiels.

Le niveau de performance attendu doit être défini à partir du niveau réel des adversaires du challenge et des résultats accessibles. Ne promets pas un taux de victoire particulier avant de l'avoir mesuré.

---

## 14. Communication avec le propriétaire

Le propriétaire souhaite une collaboration technique directe, précise et efficace.

Pour chaque étape importante, fournis :

- Le diagnostic.
- Les preuves ou résultats qui le justifient.
- La modification proposée.
- Les fichiers concernés.
- Les commandes exactes nécessaires, uniquement si elles sont utiles.
- Les résultats obtenus.
- La décision : conserver, modifier ou rejeter.

Privilégie les modifications ciblées et les résultats vérifiables.

Si tu peux inspecter ou modifier le dépôt directement, fais-le au lieu de demander à l'utilisateur de copier manuellement des fichiers ou du code.

Ne prétends jamais avoir exécuté un test si tu ne l'as pas réellement exécuté.

Ne présente jamais une amélioration comme acquise avant d'avoir obtenu des résultats fiables.

---

## 15. Première tâche à exécuter

**Ne commence pas par réécrire la stratégie.**

Commence par :

1. Inspecter l'ensemble du dépôt et identifier le point d'entrée réellement soumis à Arena.
2. Lire les fichiers des bots et les éventuels modules de connaissance, de règles et d'évaluation.
3. Vérifier les règles importantes dans le moteur installé.
4. Vérifier les différences réelles entre V1, V2, V2.1 et V2.2.
5. Reproduire les résultats de référence si les fichiers correspondants sont disponibles.
6. Identifier les trois faiblesses stratégiques les mieux étayées par le code et les replays.
7. Proposer une seule première amélioration avec un protocole de validation précis.

Présente ensuite un diagnostic court, mais suffisamment précis pour justifier le prochain changement.

**Priorité absolue : transformer le travail déjà accompli en un bot compétitif, sans repartir inutilement de zéro et sans faire perdre du temps au propriétaire avec des expériences mal contrôlées.**
