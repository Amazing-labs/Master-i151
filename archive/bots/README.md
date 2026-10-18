# Archived bots

Single-file bot versions, kept as references. The competition bot is the
modular bot in `bot/`. Results and protocol: `docs/experiments.md`.

- `bot_v1.py`: first bot (dumps high-point cards, plays eights at once).
- `bot_v2.py`: reuses the heuristics of the public `medium_bot`.
- `bot_v2_1.py`: V2 with the table suit counter fixed; base of V2.3.
- `bot_v2_2.py`: plays exactly the same games as V2 on every seed tested.
- `bot_v2_3.py`: V2.1 + continuation value within the turn. `bot/` takes
  exactly the same decisions (`tests/test_parity.py`).
