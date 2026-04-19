# Schema v0.1 — Story Quest

Contract between author layer and runtime engine. Everything in the factory is upstream (produces this) or downstream (consumes this).

## Files

- `story.schema.json` — JSON Schema (Draft 2020-12) defining a valid story.
- `story-example.json` — The Whispering Woods, ported to v0.1. This is Phase 0's canonical reference story.

## What's in a story

- **meta** — id, title, episode, reading level, cast, brief (the one-paragraph author brief is retained for audit).
- **world** — a collection of rooms plus a spawn point. v0.1 has two modes:
  - `choice-graph` (Phase 0 default): rooms traversed via named exits. Each exit can be gated by flag conditions. This matches the existing Whispering Woods UX.
  - `explore-grid` (reserved for later phases): top-down tile exploration. Rooms can optionally carry `grid` data today; the engine doesn't render it yet.
- **cast** — recurring + story-specific characters. Every character has a role, sprite ref, optional portrait, voice note, and named dialogue blocks the engine can trigger by key.
- **items** — inventory objects with kind and sprite ref.
- **flags** — typed state (`boolean` / `number` / `string`) with defaults. Flags are how rooms, puzzles, exits, and arc beats communicate.
- **arc** — ordered narrative beats. Each beat has a condition over flags; when it first becomes true, the engine shows a narrator card and fires optional effects.
- **puzzles** — each puzzle has a `type` (from a fixed vocabulary), a `config` blob, optional tiered difficulty, on-solved effects, and celebration text.
- **assets** — `library_refs` (shared library sprites this story reuses) + `manifest` (per-story assets the image pipeline will generate). Every sprite/background/portrait referenced in rooms or characters must resolve to one of these.

## Puzzle vocabulary (v0.1)

Composable primitives — the author invents fresh *content* per story, but each puzzle maps to one of these engine-supported types:

- `collect-and-deliver`
- `sequence`
- `dialogue-gate`
- `pattern-match`
- `combine`
- `navigate`
- `count-and-solve` (math)
- `word-match` (phonics)
- `sort`

Adding a primitive is a deliberate engine change. See `FACTORY_PLAN.md` §3 — this is the firewall that keeps the engine small.

## Design decision flagged for review (Gate 1)

`FACTORY_PLAN.md` envisions top-down 2D exploration (Zelda-lite). The existing `index.html` prototype is scene-graph. For Phase 0 I chose **scene-graph-first** for three reasons:

1. Whispering Woods ports with no UX rewrite — we can validate the schema now, not in a month.
2. The schema has a `grid` slot on every room already, and `world.mode` distinguishes the two. Moving to explore-grid in a later phase is additive, not a rewrite.
3. K-2 usability — discrete choice buttons are arguably a better fit than joystick-style exploration anyway; we should decide that from play-testing, not from the plan's aesthetic.

If you want explore-grid from day one, flag it and I'll rework the example (Whispering Woods would need a grid layout designed for it, which is meaningful content work).

## How to run it

```bash
# From repo root
python3 -m http.server 8000
# Open: http://localhost:8000/engine/
```

Or `open engine/index.html` directly (the engine fetches `../schema/story-example.json` relatively; `file://` works in most browsers but Chrome may need `--allow-file-access-from-files`, so a local server is the reliable path).

Click **Auto-play (test)** in the header to watch the engine walk the happy path from spawn to finale. This is the Phase 0 proof: the schema and engine are complete enough to play through without human input.

## How to validate a new story

```bash
# Schema conformance
python3 -c "
import json
from jsonschema import Draft202012Validator
schema = json.load(open('schema/story.schema.json'))
story  = json.load(open('schema/story-example.json'))
errors = list(Draft202012Validator(schema).iter_errors(story))
print('OK' if not errors else errors)
"

# Happy-path reachability (all three crystal-cave branches)
python3 engine/simulate.py
```

Both should print `OK` / `REACHED FINALE`. A full validator (cross-refs, softlocks, readability, tone) lands in Phase 2.

## What's intentionally missing in v0.1

- **Art** — the engine renders boxes and labels. Phase 1 adds the asset pipeline.
- **Adaptive difficulty across sessions** — engine tracks streak/attempts within a puzzle only; persistent adaptive state is Phase 5 polish.
- **Full reachability / softlock validator** — Phase 2 deliverable. The simulate script is a coarse stand-in.
- **Readability + tone classifiers** — Phase 2.
- **Save/resume across schema versions** — v0.1 only.

## Gate 1 — your review

Before I start Phase 1 (asset pipeline), please look at:

1. **Schema shape** — any entity missing? Anything over-modeled?
2. **Scene-graph vs explore-grid decision** (see above).
3. **Puzzle vocabulary** — the nine primitives feel right for K-2?
4. **Whispering Woods port fidelity** — does the JSON capture the story the way you'd tell it?

Next step after Gate 1 is standing up the asset pipeline and producing the shared library (Finn/Wren/Pip/tiles). That's mixed sandbox + your GPU.
