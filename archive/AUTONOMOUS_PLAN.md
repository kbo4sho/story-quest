# Story Quest — Autonomous Execution Plan

Operational companion to `FACTORY_PLAN.md`. That doc is the architecture; this one is how I actually ship it without you driving each step. Scoped to all six phases.

## What "autonomous" means here

I can run long, multi-step work unattended inside my sandbox: writing code, generating and validating schemas, building a runtime engine, wiring a packager, running test suites, and producing documentation. I pause and hand back to you at **checkpoint gates** — moments where a human decision or a host-machine action is the right next step.

Two categories of work split cleanly by where they run:

**Sandbox-only (I can do fully unattended)**
- Schema design, JSON-Schema authoring, example stories
- Runtime engine (HTML/JS Canvas, puzzle interpreters, save/load)
- Validator (schema, reachability graph, softlock detection, readability scoring)
- Packager / CLI
- Test corpus and regression suite
- Documentation

**Host-machine required (I hand off with exact instructions)**
- Local LLM inference — Ollama/llama.cpp with Qwen 2.5 or Gemma 3 on your machine
- Image generation — ComfyUI + SDXL/Flux with a style LoRA
- Any GPU-bound work

Where host work is needed I'll produce the scripts, prompts, and config that run on your side, and I'll write mocks in the sandbox so the sandboxed pieces (validator, engine, packager) can be developed and tested without waiting on your GPU.

## Checkpoint gates

I stop and ping you for review at:

1. **Schema v0.1 frozen** — before I build the engine against it
2. **Engine plays Phase 0 story** — before I start asset pipeline work
3. **Model bakeoff results** — Qwen vs Gemma, 7B vs 14B, schema-compliance rates on a fixed brief set; you pick the winner
4. **First LLM-authored story** — human review before it enters the corpus
5. **Automation loop end-to-end green** — before I generate the Phase 5 corpus
6. **Anything I find that changes the plan** — I don't quietly redesign

Outside of gates: if a phase blocks (e.g., a validator check I can't write cleanly), I'll stop and ask rather than hack around it.

## Phase-by-phase

### Phase 0 — Schema + engine skeleton (sandbox-only, ~1–2 sessions)

**Goal:** Whispering Woods, ported to JSON, playing on a minimal engine.

Deliverables:
- `schema/story.schema.json` — JSON-Schema v0.1, versioned
- `schema/story-example.json` — Whispering Woods as the canonical example story
- `engine/` — loads a spec, renders scenes, handles choices, runs one puzzle primitive end-to-end
- `engine/index.html` — harness that loads the example story
- Short `README.md` explaining how to play locally

Verification: open the harness, play through from hatch to resolution, confirm every scene beat from the current prototype still exists (choices, math puzzle, arc resolution). Diff the playthrough against `SPEC.md` for completeness.

**Gate 1: Schema frozen.**

### Phase 1 — Asset pipeline (mixed; needs your GPU)

**Goal:** visual parity with the prototype, but driven by an asset manifest.

Sandbox side (I do):
- `assets/library/` — hand-pick the shared sprites already inline-SVG'd in `index.html` (Finn, Wren, Pip, hatch, clouds, UI chrome), extract to reusable files
- `pipeline/manifest_resolver.py` — reads a story's asset manifest, checks the library cache, emits the list of prompts to generate
- `pipeline/style_prompt_template.txt` — fixed style lock prompt
- Stub generator that returns placeholder PNGs so engine tests don't block on GPU

Host side (you run, I hand off scripts):
- Install ComfyUI + SDXL or Flux with a chosen style LoRA
- Run `pipeline/generate.py` against the Phase 0 manifest
- Drop outputs into `assets/generated/`

Deliverable: Phase 0 story re-rendered with generated art, visual consistency good enough to ship to a kid.

### Phase 2 — Validator (sandbox-only)

**Goal:** a tool I can point at any story spec to get a pass/fail report.

Deliverables:
- `validator/schema_check.py` — JSON-Schema conformance
- `validator/reachability.py` — graph traversal; can the player reach the ending from spawn through every required puzzle?
- `validator/softlock.py` — no one-way door cuts off a required item
- `validator/asset_check.py` — every referenced sprite exists in library or manifest
- `validator/readability.py` — Dale-Chall on all player-facing text, K-2 threshold
- `validator/tone.py` — lightweight keyword + classifier pass for scary/sad/off-brand content
- `validator/cli.py` — one entry point that runs all checks and reports

Verification: point it at the Phase 0 spec; it should pass. Then break the spec (remove a sprite reference, add a one-way door before a required item) and confirm the right checks fail with specific errors.

### Phase 3 — Author layer v1 (host-heavy)

**Goal:** prove the LLM can produce schema-compliant stories staged through the six-step pipeline.

Sandbox side:
- `author/prompts/` — system prompt, style guide, few-shot examples (Phase 0 story)
- `author/stages/` — one prompt per stage (arc → world → NPCs → puzzles → manifest → assembly → self-critique)
- `author/orchestrator.py` — calls Ollama, runs staged generation, returns a spec
- `author/grammar.gbnf` — constrained decoding grammar for llama.cpp (fallback if model compliance is weak)
- `author/bakeoff.py` — runs the same 10 briefs through Qwen 2.5 7B, Qwen 2.5 14B, Gemma 3 7B, Gemma 3 14B; scores via the validator; emits a comparison table

Host side:
- Install Ollama, pull the four candidate models
- Run `bakeoff.py` (takes a while; uses your GPU)

**Gate 3: Model bakeoff results.** You pick the winner; I wire it into the default.

Then: author one new story (not Whispering Woods) end-to-end with the winning model. Human review, hand-patch anything the validator missed, add the patch as a regression test.

**Gate 4: First LLM-authored story.**

### Phase 4 — Automation loop (sandbox-only once Phase 3 gates clear)

**Goal:** `./factory.sh "brief sentence"` → playable HTML bundle, unattended.

Deliverables:
- `factory.sh` — orchestrates author → validator → repair loop → asset generation → packager
- `packager/bundle.py` — produces a single self-contained HTML + asset zip
- Repair loop: validator failure feeds back into author with specific errors, up to 3 rounds, then surface for human review
- End-to-end smoke test on three new briefs

**Gate 5: Automation green.**

### Phase 5 — Scale + polish (mixed)

**Goal:** 5–10 stories, a stable factory, a clear picture of where the seams are.

- Generate corpus of 10 stories from varied briefs
- Classify failures: schema drift, puzzle monotony, asset style drift, readability misses
- Tune prompts, expand puzzle primitives only where a genuine gap shows up (the firewall rule from `FACTORY_PLAN.md` §3)
- Small QA dashboard: compliance rate per phase, readability distribution, asset cache hit rate

Deliverable: story library + a short writeup of what broke and what got fixed.

## Fallbacks

- **Local model compliance is bad (< 70% schema-valid first-pass):** switch to llama.cpp with GBNF grammar constraints. If still bad, reduce to Qwen-Coder-32B (better at structured output) or degrade to a hybrid where the LLM produces prose and a rule-based assembler fills in the JSON scaffolding.
- **GPU is a bottleneck:** mock asset generation in the sandbox so I can keep building everything else. You run GPU work in batches overnight.
- **Schema turns out to be under-expressive:** version bump to v0.2 with a migration note; engine supports both for one release.
- **A puzzle primitive doesn't fit the story:** stop, don't expand the engine ad-hoc. Propose the new primitive, explain why it's different from the existing six, wait for your call.

## First concrete step

Phase 0, Schema v0.1. Two files: `schema/story.schema.json` and `schema/story-example.json` (Whispering Woods ported). Everything else is downstream of that contract.

Say the word and I'll start there.
