# Session State — 2026-04-19

Brief for picking up this project cold. For full context read `WORLD_PLAN.md` then `FACTORY_PLAN.md`.

## Where we are

**Post-planning, pre-implementation.** The vision pivoted from 2D bubble-map + 2D top-down story engine to a **3D procedurally generated exploration world** where Leo asks questions at a campfire and regions spawn around him to walk through. Planning is complete. W0 (first implementation phase) has not started.

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

**W0.** Three.js scene with:
- Flat prairie (ground plane, simple green, maybe subtle grid)
- Placeholder Finn (primitive shapes — cylinder body, sphere head, green hat — until Quaternius integration in W1)
- Tap-to-move with target marker
- Smooth third-person camera follow
- One test prop (tree or rock) for scale reference
- Touch events working on iPad; no zoom/tap-highlight

Scope is intentionally tiny. Goal: prove camera + controls feel right for a 5-year-old on a tablet. Put code in a new `world/` folder so the existing `engine/` (2D Phase 0) stays intact until 3D runtime is playable.

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
