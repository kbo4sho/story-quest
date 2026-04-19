# Session State — 2026-04-19

Brief for picking up this project cold. For full context read `WORLD_PLAN.md` then `FACTORY_PLAN.md`.

## Where we are

**W0 scaffold in place.** First Three.js scene lives at `world/index.html`: flat prairie, placeholder Finn (cylinder body, sphere head, green cone hat), one tree for scale, tap-to-move with a yellow ring target marker, smooth third-person camera follow, tablet-friendly touch (no zoom, no tap highlight). Ready for iPad playtest — open `world/index.html` directly or serve the folder over http. Next: tune controls against a real 5-year-old on a tablet (joystick fallback decision), then move to W1 (terrain gen + Quaternius kit).

## What's locked

- **Vision:** Leo walks up to a campfire, asks a question, a themed region spawns in a continuous 3D world he explores. Each region is a short learning adventure with dialogue, a puzzle, and a payoff. World accumulates with every question.
- **Visual style:** Stylized low-poly / toon (*A Short Hike* aesthetic). Asset kit: Quaternius (free, CC0) to be integrated in W1.
- **Tech:** Three.js. Tablet-first. Self-contained bundle (no build step preferred, like the existing Story Quest).
- **Two views, one world:** third-person walking view + pulled-back world-overview view. Toggle via HUD.
- **Starting state:** Small prairie with a campfire. Finn, Wren (with book), Pip present. No regions until Leo asks.
- **Vignette model (locked decisions):**
  - Implicit teaching — concept lives in dialogue + puzzle mechanics, not narration
  - Layered depth — follow-up questions add to existing regions, never regenerate
  - Four-beat climax — puzzle → character reaction → world change → celebration
  - Puzzle exercises the concept when possible, even if not on theme
  - 2–5 min fresh, collapsed on revisit (played beats skip dialogue)
- **LLM generation:** single unified structured response per question produces terrain blueprint + cast + beats. Trust the local model for factual grounding in v1.
- **What carries forward from Story Quest Phase 0:** schema as base, puzzle primitives (9 types), flag/effect/condition system, arc beats, simulate.py, author-layer prompt structure.
- **What gets retired:** 2D Canvas renderer (`engine/index.html`), tile-based world format, bubble-map shell.

## Phased roadmap (W0–W6)

- **W0** — Three.js scene, Finn walks on a prairie, tap-to-move, third-person camera. Tablet playtest.
- **W1** — Terrain gen + Quaternius prop kit + biome palettes. Hand-author one biome.
- **W2** — Port one Whispering Woods scene into a 3D region. Proves schema survives.
- **W3** — Rule-based procedural region generator from topic descriptors.
- **W4** — World-overview view + knowledge graph + campfire ask UX + region placement.
- **W5** — LLM-authored vignettes (author layer, validator, repair loop).
- **W6** — Layered depth, save/resume, polish, bundle.

## First concrete step (next action)

**W0 scaffold — done.** `world/index.html` ships all the target behaviors:
- Flat green prairie ground plane + subtle grid for motion feedback
- Placeholder Finn (cylinder body, sphere head, green cone hat, facing nose, swinging legs)
- Tap-to-move: raycast against ground, Finn walks to tap point, yellow ring target marker pulses and fades
- Smooth third-person camera follow (lerp position + look-at)
- One tree (cylinder trunk + cone canopy) for scale reference
- iPad-friendly: `touch-action: none`, no tap highlight / callout, prevents double-tap zoom and pinch gestures, viewport locked

Loaded via `<script type="importmap">` pointing at `three@0.161.0` on unpkg — no build step, matches existing Story Quest deployment style. The 2D `engine/` folder is untouched.

**Next:** iPad playtest against the target 5-year-old. Decide joystick-fallback necessity (open question #6). Then kick off W1 (procedural terrain + Quaternius kit + biome palettes).

## Open questions (flagged in WORLD_PLAN.md, decide as they become relevant)

1. Fast travel in world view — tap-a-region to teleport, or always walk?
2. Does Wren confirm questions at the campfire before region spawns?
3. Simultaneous region spawning & spatial collision rules
4. Region bounds — can they grow indefinitely, or cap and spawn adjacent?
5. Save format — localStorage vs other (confirm at W6)
6. Joystick fallback alongside tap-to-move — decide at W0 playtest
7. First-launch onboarding before any question is asked

## File layout

- `WORLD_PLAN.md` — current active plan (supersedes RABBIT_HOLE_PLAN.md and AUTONOMOUS_PLAN.md, now archived)
- `FACTORY_PLAN.md` — retained as architecture reference
- `SPEC.md` — original Story Quest Episode 1 spec (historical reference)
- `index.html` — current Story Quest game (2D)
- `world/` — 3D runtime, starting with W0 (`index.html`) — Three.js scene, tap-to-move Finn on prairie
- `engine/` — Phase 0 2D engine (`index.html`, `simulate.py`) — will be retired after 3D runtime is playable
- `schema/` — `story.schema.json`, `story-example.json` — carries forward, base for region blueprint schema
- `validator/` — Phase 0 validator work
- `assets/` — existing image assets
- `archive/` — superseded plans

## Resume protocol

A fresh Claude reading this doc should:

1. Read `WORLD_PLAN.md` (full vision + phased roadmap)
2. Read this doc (state of play)
3. Skim `FACTORY_PLAN.md` if touching author layer, validator, or asset pipeline
4. Start W0 when the user gives the go.
