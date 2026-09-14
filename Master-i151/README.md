# Mon bot i151

Projet de bot pour la compétition IA i151.

## Démarrage

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
arena test bot.py
arena match . --vs random --seed 42
arena match . --vs basic --seed 42 --games 10 --format summary
```

## Soumission

```bash
arena pack .
```

Uploadez le ZIP sur la plateforme arène.

Documentation : tutoriel et règlement dans `arena/docs/` du dépôt organisateur.
