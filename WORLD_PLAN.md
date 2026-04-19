# World Quest — 3D Procedural Learning World

*Supersedes `RABBIT_HOLE_PLAN.md` and `AUTONOMOUS_PLAN.md` (archived). `FACTORY_PLAN.md` is retained as an architecture reference — its pipeline components are reused; the product around them has changed.*

## The idea

Leo walks up to a campfire in a small prairie and asks a question. The answer manifests as a new region somewhere in a 3D world he can explore — a volcano, a coastline, a forest, a workshop. Each region is a short learning adventure: terrain, characters, and a puzzle produced by a single structured LLM response. The world accumulates with every question. Leo walks through his own curiosity.

## What Leo sees

1. Opens the app. A small prairie with a campfire in the center. Finn, Wren (holding a book), and Pip are there.
2. Walks to the campfire. A prompt invites him to ask a question.
3. He asks. In the distance, a new landmark rises — a volcano, an ocean, a bridge. A faint glow or path points toward it.
4. He walks there in third-person, or opens the world view to see the whole map and pick a direction.
5. Entering the region starts a vignette: dialogue, a puzzle, a payoff moment.
6. The region stays. Revisiting is welcome. Asking a follow-up question layers more onto it.

## Two views

- **Walking view** — third-person camera over Finn. Tap-to-move primary; virtual joystick as an optional toggle. Auto-interact when close to a thing.
- **World view** — pulled-back orbital / high-angle, shows the whole terrain with region labels. Toggle via HUD button. Used for navigation and for seeing the shape of what Leo has explored. Fast travel TBD (see open questions).

Both views share one continuous world. No scene loads between them — just camera transitions.

## Visual style

Stylized low-poly / toon — *A Short Hike* aesthetic. Soft silhouettes, flat shading, warm palette. Assets from a shared low-poly kit (Quaternius recommended: free, CC0, matches the style closely). Per-topic palette swaps and prop-weight shifts give each biome its own feel without bespoke art.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     WORLD SHELL                         │
│                                                         │
│  ┌───────────┐   ┌──────────┐   ┌──────────────────┐    │
│  │ Campfire  │──▶│ Knowledge │──▶│ Region Placer    │    │
│  │ (ask UX)  │   │  Graph    │   │ (clustering +     │    │
│  └───────────┘   └──────────┘   │  world layout)    │    │
│                                  └────────┬─────────┘    │
│                                           │              │
│                                           ▼              │
│  ┌────────────────────────────────────────────────┐     │
│  │             VIGNETTE FACTORY                   │     │
│  │                                                │     │
│  │  Q&A  ──▶  Author Layer  ──▶  Unified Region   │     │
│  │           (local LLM)         Blueprint        │     │
│  │                                   │            │     │
│  │  Validator ◀──────────────────────┘            │     │
│  │      │                                         │     │
│  │      ▼                                         │     │
│  │  Prop Kit + Palette ──▶ Populated 3D Region    │     │
│  └────────────────────────────────────────────────┘     │
│                         │                                │
│                         ▼                                │
│  ┌────────────────────────────────────────────────┐     │
│  │              3D RUNTIME ENGINE                 │     │
│  │  Three.js. Third-person + world view.          │     │
│  │  Plays any region blueprint.                   │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

Three layers:

1. **Shell** — the prairie, the campfire, the knowledge graph, the region placer. Tracks what Leo has asked and where everything lives spatially.
2. **Factory** — takes a Q&A pair and produces a unified region blueprint (terrain + cast + beats in one structured response). Story Factory pipeline adapted for this input.
3. **Engine** — Three.js runtime. Renders terrain, controls the camera, plays beats. One engine; any blueprint.

## The vignette model

Each region contains one **learning adventure** — a seeded sandbox of beats, not a linear story. Leo walks in. Things are interactable. Beats fire based on what he does.

Design principles (locked):

- **Implicit teaching.** The concept lives in dialogue and puzzle mechanics. No narrator-as-teacher voice. Authoring constraint baked into the LLM prompt.
- **Layered depth.** Follow-up questions *add* NPCs, landmarks, or beats to the existing region. Nothing regenerates. The world accumulates.
- **Four-beat climax.** Puzzle resolves → character reaction → world-change moment → celebration. Separate beats, not one.
- **Puzzle exercises the concept.** The primitive is chosen to best exercise the answer even when not perfectly on theme. Pedagogy first, thematic fit second.
- **2–5 min fresh, collapsed on revisit.** Played beats skip dialogue; NPCs wave; puzzles remain replayable if Leo wants.

## Unified LLM generation

One structured response per question produces the whole region. Rough shape (not final — Phase W5 locks it):

```json
{
  "topic": "volcanoes",
  "concept": "pressure builds up, then releases",
  "biome": {
    "base": "rocky_mountain",
    "palette": "ember",
    "landmarks": [
      { "type": "mountain", "tag": "the_volcano", "scale": "large" },
      { "type": "lava_pool", "count": 2 }
    ],
    "prop_weights": { "dead_tree": 0.8, "rock_large": 1.5 }
  },
  "cast": [
    { "id": "fiora", "kind": "fire_spirit", "role": "guide", "anchor": "volcano_base" }
  ],
  "beats": [
    { "id": "hook",    "trigger": "enter_region",     "dialogue": [...] },
    { "id": "learn",   "trigger": "approach:fiora",   "dialogue": [...] },
    { "id": "puzzle",  "trigger": "after:learn",      "puzzle": { "type": "pattern-match", ... } },
    { "id": "react",   "trigger": "after:puzzle",     "dialogue": [...] },
    { "id": "change",  "trigger": "after:react",      "effect": "safe_eruption" },
    { "id": "resolve", "trigger": "after:change",     "dialogue": [...] }
  ],
  "completion": "beat:resolve"
}
```

Grounding: trust the local model. No external fact-check layer in v1. Reading level + tone checks from the existing validator still apply. Revisit if quality drops.

## Starting state

Small prairie. Warm grass, soft hills, a campfire at the center. Finn, Wren (with book), Pip present. No regions yet. On first launch Leo can walk around, meet the characters, and find the campfire. Wren prompts: *"Ask anything, and we'll go see."*

## Phased roadmap

Each phase is a working product. Each is a strict superset of the previous.

### W0 — 3D shell
Three.js scene. Finn model on a flat prairie. Tap-to-move. Third-person camera follow. One test prop. *Proves controls feel right for a 5-year-old on a tablet.*

### W1 — Terrain + prop kit
Procedural heightmap, biome palettes, Quaternius kit integrated. One hand-authored biome (the prairie + one other) to validate the look. Instanced rendering for prop density.

### W2 — Hand-authored region with vignette
Port one Whispering Woods scene into a 3D region. Dialogue system, one puzzle primitive rendered in 3D, four-beat climax. Proves the schema survives the dimensional jump.

### W3 — Procedural region generator
Rule-based (no LLM yet): topic descriptor → biome blueprint → populated 3D region. Author 5 topic descriptors by hand to test variety.

### W4 — World view + knowledge graph
World-overview camera toggle. Knowledge graph drives region placement. Clustering places related topics near each other. Campfire UX: Leo asks a question, a region spawns at the right spatial slot, a path lights up.

### W5 — LLM-authored vignettes
Author layer generates unified region blueprints from Q&A. Validator gates (reachability, readability, solvability). Repair loop on failure.

### W6 — Layered depth + polish
Follow-up questions layer onto existing regions (new beat/NPC/landmark appended, not regenerated). Save/resume via localStorage. Tablet performance pass. Bundle as a self-contained deliverable.

## What carries forward from Story Quest Phase 0

| Artifact | Role in World Quest |
|---|---|
| `story.schema.json` | Base for the region blueprint schema. Terrain section replaced with 3D biome spec; beats structure intact. |
| Puzzle primitives (9 types) | Reused. Each gets a 3D rendering adapter in W2. |
| Flag / effect / condition system | Unchanged. Drives vignette state and meta-state across the map. |
| Arc beats | Repurposed as vignette beats with triggers. |
| `simulate.py` | Adapted for beat-graph reachability on the new schema. |
| Author-layer prompt structure | Adapted — input is Q&A, output is a unified blueprint. |

## What gets retired

- 2D Canvas renderer (`engine/index.html`) — replaced by Three.js runtime.
- Tile-based world format.
- Bubble-map shell from `RABBIT_HOLE_PLAN.md` — everything is 3D now.
- The `AUTONOMOUS_PLAN.md` phased roadmap — replaced by W0–W6.

## Open questions

1. **Fast travel in world view** — tap-a-region to teleport, or always walk? Walking feels more like a world; teleport feels more like a menu. Lean: tap-to-walk-there with time-skip animation, not instant teleport.
2. **Campfire ask UX** — does Wren read the question back to confirm before the region spawns? Useful for a 5-year-old; adds a turn.
3. **Simultaneous region placement** — two new questions in quick succession: do both spawn, or queue? Spatial collision rules.
4. **Region bounds** — can a region grow indefinitely with follow-up questions, or does it cap and a *new* related region spawn adjacent once full?
5. **Save format** — knowledge graph + region cache + Leo's position + played beats. LocalStorage likely sufficient; confirm at W6.
6. **Joystick necessity** — tap-to-move is primary, but is a joystick needed as a fallback for dense terrain? Decide at W0 playtest.
7. **First-launch onboarding** — before any question, what does Leo *do*? Walk around, meet characters, Pip chases a butterfly, Wren points at the campfire? Needs to teach the ask-loop without words.

## First concrete step

**W0.** A Three.js scene with Finn walking on a prairie. No terrain gen, no regions, no questions. Just camera feel and tap-to-move controls, tested on a tablet. Tight scope, fast feedback loop.

Say the word and I'll start there.
