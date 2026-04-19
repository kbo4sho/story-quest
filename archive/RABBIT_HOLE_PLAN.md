# Rabbit Hole — Merged Product Plan

*Supersedes `AUTONOMOUS_PLAN.md` (standalone Story Factory). `FACTORY_PLAN.md` is retained as architecture reference — its pipeline components are reused, but the product around them has changed.*

## The idea

Leo asks questions. Those questions become a living, explorable world. Each interest — dinosaurs, volcanoes, how bridges work — grows into a region on a map that Leo can walk through and play inside. The deeper he goes down any rabbit hole, the richer and more game-like that region becomes.

Two existing projects merge to make this:

- **Rabbit Hole** (current prototype) — a question-answer visualizer. The main screen is a field of bubbles, each with an image and a subtitle representing something Leo asked about.
- **Story Quest** (Phase 0 complete) — an interactive story engine with a JSON schema, flag-based state, 9 puzzle primitives, a narrator arc system, and a working runtime that plays through branching stories.

The merged product keeps Rabbit Hole as the *outer shell* (the map of interests) and uses Story Quest's engine as the *inner experience* (what happens when you step inside a region).

## What Leo sees (end state)

1. **The World Map** — a top-down explorable canvas. Regions are clustered by topic. A cluster about "ocean animals" might sit near "boats" which sits near "pirates." The map grows over time as Leo asks new questions.

2. **Regions** — each region has a visual biome (jungle, underwater, space, medieval, etc.) generated from the topic. Walking into a region loads a short, playable vignette — a 2–5 minute interactive experience with narration, a puzzle or two, and characters who talk about the topic.

3. **The Cast** — Finn, Wren, and Pip travel with Leo across the map. They show up inside vignettes as guides, puzzle-helpers, and narrators, just like in Story Quest. New characters are topic-specific NPCs generated per-region.

4. **Growth** — revisiting a region after asking follow-up questions deepens it. A "volcanoes" region that started as a single room with a matching puzzle might grow a second room with a cross-section diagram you can label, then a third with an eruption simulation.

## Four-layer evolution

We don't build the end state in one shot. Each layer is a working product Leo can use, and each layer is a strict superset of the previous one.

### Layer 0 — Bubbles (Rabbit Hole as-is)
*What exists today.* A flat field of bubbles. Tap a bubble, get an answer. No spatial relationships, no exploration.

**What we keep:** the question-answer loop, the bubble visual identity, the image generation for each topic.

### Layer 1 — Positioned bubbles on a canvas
Bubbles get (x, y) coordinates. Related topics cluster together (simple force-directed layout or manual placement). Pan and zoom. Still tap-to-view, but now there's a sense of geography — "ocean stuff is over here, space stuff is over there."

**New tech:** a 2D canvas with pan/zoom, a clustering algorithm (even k-means on topic embeddings would work), persistent positions stored in a JSON file.

### Layer 2 — Biome regions
Clusters become visually distinct regions with generated background art. The canvas becomes a map. Walking between regions (or tapping) shows a transition. Each region has a mood, color palette, and terrain style derived from its topic.

**New tech:** Story Quest's asset pipeline generates region backgrounds. The `world.mode: explore-grid` path in the schema activates — each region is a room with a background, characters present, and narration on entry.

### Layer 3 — Playable vignettes inside nodes
Entering a region launches a mini Story Quest experience. A local LLM authors a short vignette (1–3 rooms, 1–2 puzzles) from the question-answer content. The full puzzle vocabulary is available. Vignettes are cached — regenerated only when new questions deepen the topic.

**New tech:** Story Quest's author layer generates vignettes from Q&A content instead of from a creative brief. The runtime engine plays them. The validator ensures they're solvable.

## How Phase 0 work carries forward

Almost everything from Story Quest Phase 0 is reused:

| Phase 0 artifact | Role in Rabbit Hole |
|---|---|
| `story.schema.json` | Schema for vignettes. Mostly unchanged — vignettes are just short stories. May add a `vignette` flag to meta or relax `estimated_playtime_minutes` minimum. |
| `story-example.json` | Becomes a test fixture. Whispering Woods is too long for a vignette, but validates that the engine can handle rich content. |
| Runtime engine (`engine/index.html`) | Plays vignettes when a region is entered. Loaded as an iframe or integrated directly into the map shell. |
| `simulate.py` | Validates vignette reachability. Runs unchanged on any schema-compliant vignette. |
| Puzzle primitives (9 types) | Available for vignettes. The author layer picks 1–2 per vignette based on the topic (e.g., `count-and-solve` for a math-adjacent topic, `sort` for classification, `word-match` for vocabulary). |
| Flag/effect/condition system | Drives state within a vignette and also the *meta-state* across the map (which regions Leo has visited, which are "deepened"). |
| Arc beats | Narrator cards in vignettes. Also usable for map-level milestones ("You've explored 5 regions — Pip has a surprise!") |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   RABBIT HOLE SHELL                  │
│                                                      │
│  ┌───────────┐   ┌──────────┐   ┌────────────────┐  │
│  │ Question   │──▶│ Knowledge │──▶│ Map / Region   │  │
│  │ Interface  │   │ Graph     │   │ Manager        │  │
│  └───────────┘   └──────────┘   └───────┬────────┘  │
│                                         │            │
│                        ┌────────────────┘            │
│                        ▼                             │
│  ┌──────────────────────────────────────────┐        │
│  │           VIGNETTE FACTORY               │        │
│  │                                          │        │
│  │  Q&A Content ──▶ Author Layer ──▶ Schema │        │
│  │                  (local LLM)      JSON   │        │
│  │                                    │     │        │
│  │  Validator ◀───────────────────────┘     │        │
│  │      │                                   │        │
│  │      ▼                                   │        │
│  │  Asset Pipeline ──▶ Vignette Bundle      │        │
│  └──────────────────────────────────────────┘        │
│                        │                             │
│                        ▼                             │
│  ┌──────────────────────────────────────────┐        │
│  │           STORY QUEST ENGINE             │        │
│  │  (plays any vignette bundle)             │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

Three layers:
1. **Shell** — the map, the question interface, the knowledge graph that tracks what Leo has asked. This is the Rabbit Hole side.
2. **Factory** — takes Q&A content and produces playable vignettes. This is the Story Factory pipeline (author → validator → assets → packager), now fed by questions instead of creative briefs.
3. **Engine** — plays vignettes. This is Story Quest's runtime, unchanged.

## Knowledge graph

The bridge between "Leo asked a question" and "a region exists on the map." Each node in the graph is a topic. Edges are relationships (asked-about, related-to, deepened-by). Properties on each node:

- `topic` — short label ("volcanoes")
- `questions` — list of Q&A pairs Leo has asked about this topic
- `region_id` — pointer to the map region (null until Layer 2)
- `vignette_id` — pointer to the generated vignette (null until Layer 3)
- `depth` — how many questions Leo has asked in this area (drives vignette richness)
- `position` — (x, y) on the map canvas
- `cluster` — which topic cluster this belongs to
- `biome` — visual theme derived from the topic

The graph is the single source of truth. The map reads it to render regions. The factory reads it to generate vignettes. The shell writes to it when Leo asks questions.

## Phased roadmap

### Phase R0 — Knowledge graph + positioned bubbles (Layer 1)
*Sandbox-buildable. No LLM, no GPU.*

Take the existing Rabbit Hole bubble view and give it structure:
- Define the knowledge graph schema (a simple JSON file)
- Port existing Q&A content into the graph
- Build a canvas renderer with pan/zoom that reads the graph and places bubbles
- Implement basic clustering (topic-embedding similarity, force-directed layout)
- Tap a bubble → shows the Q&A answer (existing behavior, now on a canvas)

**Deliverable:** Rabbit Hole with a spatial map instead of a flat list. Still bubbles, but now with geography.

**Gate R0:** Does the map feel like an explorable space? Does clustering make sense to Leo?

### Phase R1 — Biome regions + visual polish (Layer 2)
*Needs asset pipeline (GPU for image gen).*

- Clusters become named regions with generated background art
- Implement region transitions (walk or tap to move between regions)
- Each region has a narration-on-enter from the knowledge graph content
- Characters (Finn, Wren, Pip) appear on the map and inside regions
- Wire up Story Quest's asset pipeline to generate region backgrounds from topic descriptions

**Deliverable:** A visual world map where walking into "ocean animals" loads an underwater-themed region with a short narration about what Leo has learned.

**Gate R1:** Visually coherent? Transitions smooth? Does it feel like a world?

### Phase R2 — Vignette generation (Layer 3)
*Needs local LLM + asset pipeline.*

- Adapt the author layer: input is Q&A content from the knowledge graph, not a creative brief
- Author layer produces a 1–3 room vignette with 1–2 puzzles matched to the topic
- Validator ensures solvability and reading level
- Vignettes are cached per-region, regenerated when depth increases
- Runtime engine plays vignettes when Leo enters a region

**Deliverable:** Entering a region launches a playable mini-experience. Leo learns through play.

**Gate R2:** Are generated vignettes fun? Do puzzles feel connected to the topic? Is the reading level right?

### Phase R3 — Growth + meta-progression
*Mostly sandbox. Some LLM.*

- Revisiting a topic after new questions triggers vignette regeneration with richer content
- Map-level arc beats ("You've explored 5 regions!" → Pip celebration)
- Cross-region connections (a "boats" vignette references what Leo learned in "ocean animals")
- Adaptive difficulty across vignettes based on Leo's puzzle performance history

**Deliverable:** A world that grows and deepens with Leo's curiosity.

### Phase R4 — Polish + content depth
- Generate 10+ regions from Leo's actual questions
- Tune the author layer for vignette quality
- Asset consistency pass (all regions feel like the same game)
- Save/resume across sessions
- Performance tuning for tablet

## What I need from you to start

1. **Rabbit Hole code / screenshots** — I need to see the current prototype to understand the bubble UI, data format, and tech stack. Even a screenshot + "it's a React app" or "it's vanilla HTML" would unblock Layer 1 design.

2. **Leo's existing Q&A content** — the questions he's already asked and the answers generated. This becomes the seed data for the knowledge graph.

3. **Tech stack preference** — should the merged product be a single HTML app? An Electron app? A tablet-first web app? The answer shapes how the map shell and the Story Quest engine integrate.

## What I can start now (no blockers)

Even before seeing the Rabbit Hole prototype:
- **Knowledge graph schema** — define the JSON structure for topics, questions, clusters, and region pointers
- **Map canvas renderer** — a pan/zoom canvas that reads a graph and renders positioned nodes with topic images
- **Clustering algorithm** — given topic labels + optional embeddings, produce (x, y) positions and cluster assignments
- **Vignette schema variant** — adapt `story.schema.json` for short-form vignettes (relax playtime, add topic metadata, add depth field)

These are all sandbox work. They produce testable artifacts that plug into whatever the Rabbit Hole prototype looks like.

## Relationship to existing plans

- `FACTORY_PLAN.md` — the six-component architecture (schema, author, validator, asset pipeline, packager, engine) is intact. The "factory" now produces vignettes instead of full stories, fed by Q&A content instead of creative briefs. The components are the same; the input and scale change.
- `AUTONOMOUS_PLAN.md` — stale. The phased roadmap above replaces it. The checkpoint-gate model carries over (I build what I can in sandbox, hand off GPU/LLM work with scripts).
- Phase 0 deliverables — fully reusable. Schema, engine, simulator, puzzle primitives all carry forward.

## Open questions

1. **Bubble-to-region transition UX** — do bubbles gradually morph into regions as content accumulates, or is there a clear threshold ("3 questions about volcanoes → volcanoes becomes a region")?
2. **Question interface location** — is there a persistent "ask" bar on the map, or does Leo ask questions inside regions (or both)?
3. **Multiplayer / sharing** — does Leo's map stay private, or can he share regions / vignettes with friends?
4. **Rabbit Hole's current answer generation** — what produces the answers today? An API call to an LLM? A search? Understanding this determines how the knowledge graph gets populated.
5. **Offline vs online** — the Story Factory was designed for fully local/offline operation. Does Rabbit Hole need network access for answer generation, or should everything run locally?
