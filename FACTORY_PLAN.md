# Story Quest — Story Factory Plan

A framework for producing interactive, narrative-driven exploration games for K-2 kids. The current `SPEC.md` / `index.html` ("The Whispering Woods") becomes **one artifact** of this pipeline, not the product itself.

## Product definition

**What the factory produces:** self-contained, tablet-playable interactive stories. Each story features:

- Finn, Wren, and Pip as recurring cast
- A fresh setting and three-act narrative (beginning, middle, end with real resolution)
- Top-down 2D free exploration (Zelda-lite)
- 2–3 custom puzzles woven into the story
- K-2-appropriate reading level, touch targets, and gentle failure
- AI-generated art drawn from a shared asset library for visual consistency

**What the factory is:** a data-driven system where a local LLM (Qwen / Gemma) authors stories into a strict schema, an image pipeline fulfills the asset manifest, and a shared runtime engine plays any story that conforms to the schema.

## Architecture at a glance

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Author Layer    │    │  Validator       │    │  Asset Pipeline  │
│  (Qwen / Gemma)  │───▶│  (schema + QA)   │───▶│  (image gen +    │
│  Brief → Spec    │    │                  │    │   library cache) │
└──────────────────┘    └──────────────────┘    └────────┬─────────┘
                                                         │
                                                         ▼
                                               ┌──────────────────┐
                                               │  Packager        │
                                               │  (bundle engine  │
                                               │  + spec + art)   │
                                               └────────┬─────────┘
                                                        │
                                                        ▼
                                               ┌──────────────────┐
                                               │  Runtime Engine  │
                                               │  (plays any      │
                                               │  conforming      │
                                               │  spec)           │
                                               └──────────────────┘
```

The engine is fixed. Everything upstream produces data that the engine consumes.

## The six components

### 1. Story Schema (the contract)

The most important artifact in the system. Everything else is built to produce or consume it. A story is a JSON document with:

- **Meta:** title, episode number, cast present, estimated playtime, reading level
- **World:** grid-based map (tiles, walkable flags), room definitions with exits, spawn point
- **NPCs:** position, sprite reference, dialogue trees, quest flags they gate
- **Items:** inventory objects with pickup/use semantics
- **Arc beats:** ordered list of narrative checkpoints tied to world state (e.g., "Act 1 end: Pip follows you into the cave")
- **Puzzles:** each puzzle is a self-contained block with `type` (one of a few engine-supported primitives — see §3), a `config` blob, a `solved_effect` that mutates world state, and a `solved_text` line
- **Asset manifest:** every image the story needs, with style tags, required dimensions, and a slot in the library (see §5)
- **Flags:** named boolean/numeric state the story reads and writes

This schema is versioned. The engine declares which schema version it supports; author output must match.

### 2. Author Layer (local LLM)

**Model:** Qwen 2.5 (7B or 14B) or Gemma 3 running locally via Ollama/llama.cpp. Gemma tends to be more verbose; Qwen tends to be better at structured output — benchmark both on schema-compliance rate before committing.

**Input:** a one-paragraph brief. Example: _"A story in a seaside tide-pool village. Finn is afraid of water. Main puzzle is trading shells to a crab merchant. Resolution: Finn wades in to save Pip."_

**Output:** a complete story spec (JSON) + asset manifest.

**How it stays on the rails:**
- **Prompt scaffolding:** a master system prompt loads the full schema, a style guide (K-2 reading level, Finn/Wren/Pip voices, pacing rules), and 2–3 few-shot examples of past stories.
- **Staged generation** instead of one-shot. The author produces the story in a pipeline of smaller calls:
  1. Arc outline (3-act beats, 4–6 sentences each)
  2. World map + rooms
  3. NPC roster + dialogue
  4. Puzzle designs (2–3)
  5. Asset manifest
  6. Final assembly + consistency pass
- **Constrained decoding / grammar** where the runtime supports it (llama.cpp GBNF grammar) so the model physically cannot emit malformed JSON.
- **Self-critique pass:** after assembly, the same model re-reads its own spec against a checklist and patches issues.

### 3. Puzzle authoring (custom per-story, constrained primitives)

"Custom per story" doesn't mean "free-form code." The author invents puzzle _content_ and _framing_ fresh each time, but each puzzle must be expressible via a small set of engine primitives. This gives variety without letting the engine become unbounded. Starting primitives:

- **Collect-and-deliver:** gather N items matching a predicate, bring to an NPC
- **Sequence:** interact with objects in a specific order
- **Dialogue-gate:** answer an NPC's question correctly (multiple choice or matching)
- **Pattern-match:** complete a visual pattern (colors, shapes, counts)
- **Combine:** use item A on object B to produce effect C
- **Navigate:** reach a hidden location by reading environmental clues

The author composes these into a fresh puzzle each story — e.g., "gather three tide-pool creatures, identify which one is nocturnal (dialogue gate), trade it to the crab merchant (deliver)." The engine has never seen that specific puzzle, but every step maps to a known primitive.

When a story genuinely needs something new, adding a primitive is a deliberate engine change, reviewed and versioned. This is the firewall that keeps the engine small.

### 4. Validator

Runs after authoring, before assets are generated (assets are expensive — fail fast). Catches:

- **Schema conformance:** JSON structure, required fields, types
- **Reachability:** can the player actually get from spawn to the ending through every required puzzle? (Graph traversal over rooms + flag dependencies)
- **Softlock detection:** no state where progress is impossible (e.g., a required item is only available before a one-way door)
- **Asset completeness:** every referenced sprite/background/portrait is in the manifest
- **Readability:** all player-facing text scores at K-2 level (Dale-Chall or similar)
- **Safety / tone:** a lightweight classifier pass for anything scary, sad, or off-brand for K-2

Validator failures loop back to the author layer with specific error messages. Budget: up to 3 repair rounds before human review.

### 5. Asset pipeline

**Two tiers:**

- **Shared library** — canonical assets that every story reuses: Finn, Wren, Pip character sprites (8-direction walk cycles), UI chrome, common tiles (grass, path, water, stone). Authored once by hand or with careful human-in-the-loop generation, locked to a style.
- **Per-story generated** — backgrounds, NPC portraits, unique props, puzzle art. Generated on demand from the asset manifest.

**Generator:** Stable Diffusion XL or Flux, local via ComfyUI. A fixed style LoRA or reference-image pipeline keeps output visually consistent across stories. Every generated asset is tagged and cached — if a later story asks for "friendly crab NPC, pastel, storybook," the cache hits and skips regen.

**Style lock:** the asset prompt template is fixed (e.g., _"{subject}, top-down ¾ view, storybook illustration, flat pastel palette, soft outlines, K-2 friendly, no text"_). The author layer fills `{subject}`; everything else is enforced.

### 6. Runtime engine

Fixed. Written once. Plays any conforming story. Responsibilities:

- Loads story spec + asset bundle
- Renders top-down 2D world (Canvas 2D is plenty at this scale; WebGL unnecessary)
- Handles input (touch + keyboard)
- Dialog box + choice UI
- Inventory UI
- Puzzle interpreter — one module per primitive (§3)
- Save/resume via localStorage
- Arc-beat triggers (narrator card appears when flag X flips)
- Accessibility: large touch targets, high contrast, optional narration audio

## Phased roadmap

A sensible build order that keeps the system playable at every step.

**Phase 0 — Schema + engine skeleton.** Write the schema v0.1. Build a minimal engine that loads a _hand-written_ JSON story and plays it. Ship one hand-authored story end-to-end. No LLM, no image gen. This validates the schema is expressive enough. _Deliverable:_ one playable story, hand-authored.

**Phase 1 — Asset pipeline.** Stand up local image gen. Produce the shared library (Finn/Wren/Pip sprites, core tiles). Build the manifest-to-asset batch script with caching. Re-skin the Phase 0 story with generated art. _Deliverable:_ a visually polished version of the Phase 0 story.

**Phase 2 — Validator.** Build schema validator, reachability checker, readability scorer. Run it against the Phase 0 spec and fix whatever it catches. _Deliverable:_ a tool you can point at any story spec to get a pass/fail report.

**Phase 3 — Author layer v1.** Integrate Qwen/Gemma. Start with the staged pipeline (§2) but with heavy human review at each stage. Author one new story — _not_ Whispering Woods — to prove the pipeline isn't overfit. _Deliverable:_ second story, mostly LLM-authored, human-edited.

**Phase 4 — Automation loop.** Wire author → validator → repair → assets → package into one script. Target: `./factory.sh "brief sentence"` produces a playable HTML bundle unattended. _Deliverable:_ CLI that produces stories from briefs.

**Phase 5 — Scale + polish.** Generate 5–10 stories. Use the corpus to find failure patterns. Tune prompts, expand puzzle primitives where justified, improve asset consistency. _Deliverable:_ a library of stories and a stable factory.

## Open questions worth deciding early

- **Which local model:** Qwen 2.5 vs Gemma 3, 7B vs 14B. Worth a one-afternoon bakeoff on schema-compliance rate before investing in prompt tuning.
- **Asset determinism:** do we want a fixed seed per story so regeneration is reproducible, or embrace variation?
- **Distribution format:** standalone HTML bundle per story (current direction) vs. a single "player" app that loads story packs. The latter scales better if you ever want a library view.
- **Where "Whispering Woods" (the existing work) lives:** is it retired, or do we port it to the new schema as the canonical reference story? Recommend porting — it becomes the Phase 0 hand-authored spec.

## First concrete next step

If you want to start moving on this: **draft Schema v0.1** as a single JSON example plus a JSON-Schema file describing the structure. Everything else — engine, author prompts, validator — is downstream of that contract. I can draft it whenever you're ready.
