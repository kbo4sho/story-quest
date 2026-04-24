# Story Quest — Designer Agent Plan

> Written 2026-04-22. Captures the authoring layer of the game: a long-running
> LLM agent whose job is to make each concept world continuously better. Pairs
> with `GARDEN_PLAN.md` (the player-experience layer) and
> `SUBSTRATE_PLAN.md` (the storage model). Retires the "worldtender" framing
> from GARDEN_PLAN — the tender was too modest a version of this.

## What the agent is, in one sentence

A long-running LLM agent whose single job is to make one concept world —
"electricity", "ocean", "dinosaurs" — continuously deeper, more
interesting, and more fun to explore. It authors, it evaluates its own
work, and it iterates. Kids never see the agent; they explore the world
it tends.

## The pitch

Most LLM-game experiments put the model in the request path: kid asks,
model responds. That frames the model as a reactor, caps quality at
whatever can be generated in one request, and produces a new wall of
content every time. Quality doesn't compound. It starts over.

The Designer Agent inverts this. The model is the *author*, running in
the background, always. The electricity world exists as a persistent
canon that the agent improves across hundreds of passes. The agent
evaluates its own prior work against a rubric, fixes what it flagged,
connects loose ends, adds new variety, prunes dead weight. Month over
month, the electricity world becomes genuinely deeper — not because any
one kid asked a better question, but because the agent has been patient
and iterative.

The kid is an **explorer** of this world. They arrive at a tiny slice,
unlock more by asking and doing and noticing, and find the world always
has more room to poke into. A kid who returns after six months finds
electricity richer than they left it, even in the parts they'd already
explored.

## The two-layer frame

```
SUPPLY (this doc)                        DEMAND (GARDEN_PLAN)
designer agent                           the explorer
    │                                         │
    │ writes canon                            │ reads canon (filtered)
    ▼                                         ▼
┌────────────────────────────────┐     ┌─────────────────────┐
│  canon/concepts/electricity/   │ ──► │ kid's unlocked view │
│  canon/concepts/ocean/         │     │ kid's journal       │
│  canon/concepts/dinosaurs/     │     │ kid's bag           │
│  ...                           │     │ kid's flags         │
└────────────────────────────────┘     └─────────────────────┘
```

The **canon is the API boundary**. The agent writes to it. The player
layer reads from it, filtered by what the kid has unlocked. They never
talk to each other directly — canon is the only shared surface.

## The three passes

The agent rotates through three pass types. Each run picks one concept
and one pass type.

### 1. Generate — add new content
Author new entities to extend the concept. The rubric gates what
survives.

- **NPC.** Real historical figure, mythological figure, personified
  creature, themed character.
- **Affordance.** Interactive object — lever, pedestal, bell, vent,
  planter, combine-slot. Must teach through its consequences, not through
  a plaque.
- **Hidden thing.** Note, item, sealed door, glinting object. Found only
  by exploration.
- **Sign.** Readable, reading-level-appropriate. The vocabulary surface.
- **Thread.** Conditional reaction tying this concept to another
  (spark-crystal from electricity → anglerfish in ocean).
- **Sub-region.** A new walkable corner inside the concept. Rare; only
  when the main region is mature enough to warrant a second gathering
  spot.
- **Puzzle.** Environmental, experimental, no locked answer the kid has
  to be *told*.

Output: a patch proposing new entities. Pipeline validates against canon
schema and rubric, then applies.

### 2. Evaluate — score what exists
Read the concept's current canon. Score each entity against the rubric.
Produce an explicit improvement list.

Examples of what Evaluate catches:
- "NPC X has 6 lines but 5 of them overlap in meaning." → redundancy,
  prune 4.
- "Affordance Y sets no flags and leads nowhere." → dead end, reconnect
  or prune.
- "Sign Z uses 4th-grade vocabulary." → rewrite at K-2.
- "Concept has 8 scientist-type NPCs and zero mystical figures." →
  variety gap, plan a future Generate.
- "Thread W has prereqs that are impossible to satisfy given the current
  affordance graph." → broken, fix or remove.
- "Region has 12 affordances within a 10-unit radius." → clutter, thin.

Output: `quality.json` written back to the canon with current ratings +
a prioritized improvement list the next Iterate pass (or a human) can
act on.

### 3. Iterate — apply the fixes
Read the improvement list. Rewrite low-scorers, prune the dead,
reconnect orphaned things, merge redundancies, repair broken threads.

- "Rewrite sign Z at K-2." → new sign text, validated.
- "Prune Edison lines 3, 4, 5 — redundant." → pruned, reflected in
  entity file.
- "Connect affordance Y to thread_eels" → thread fires when Y's flag is
  set.
- "Merge sub-regions A and B — too similar." → one survives, the other's
  best content folds in.

Output: patches to existing canon entities. Same schema as Generate,
targeting existing IDs.

## The rubric

The agent's system prompt carries the current rubric plus "good" and
"bad" examples per criterion. Tunable over time.

| Criterion | What it means | How we score |
|---|---|---|
| **K-2 reading level** | Concrete vocabulary, short sentences, no jargon undefined | Dale-Chall ≤ 5.0, sentence length ≤ 12 words median |
| **Teaches a real principle** | A true, age-appropriate thing about the concept | LLM self-check against a "what principle does this reveal?" prompt |
| **Invites noticing, not telling** | Kid *does*, then truth becomes visible. NPCs gesture, don't lecture. | Ratio of affordance-consequences to NPC-paragraphs. Rubric prefers 3:1 or better. |
| **Coherent with canon** | Doesn't contradict `world.json` canonical entities or established contradictions | Cross-check against entity list + contradiction log |
| **Surprise & discoverability** | Hidden things are genuinely unadvertised. Affordances reveal purpose through use. | Hidden items must have no dialogue-hint pointer. Affordances must have `reveals_on_use` field populated. |
| **Warm tone** | Curious, friendly, specific. Never scary, sad-for-sadness, preachy. | Tone classifier pass + sample human review |
| **Variety** | Different perspectives (scientist + artist + mythological + child). No one archetype dominates. | Count archetypes across NPCs per concept. Rubric flags > 50% of one type. |
| **Pacing** | Region feels alive, not cluttered or sparse. | Target: 3–5 NPCs, 3–6 affordances, 2–4 hidden per active sub-region |

## Canon shape

Each concept gets a directory. Everything addressable. Every change
logged. The agent can read its own history to learn "I added 3
scientists recently, time for a mystic."

```
canon/
  concepts/
    electricity/
      world.json           ← the bible (tone, motifs, canonical entities,
                              open hooks, contradiction log)
      entities/
        npc_edison.json
        npc_volta.json
        npc_zira.json
        ...
      affordances/
        coil_lever.json
        material_pedestal.json
        ...
      hidden/
        volta_note.json
        spark_crystal.json
        ...
      signs/
        workshop_sign.json
        ...
      threads/
        thread_eels.json    ← unlock condition + payload
        ...
      regions/              ← sub-regions inside the concept
        edisons_workshop.json   ← the seed region
        ...
      history/
        gen_pass_0001.json  ← every agent pass, for audit + replay
        gen_pass_0002.json
        ...
      quality.json          ← current ratings, last evaluated timestamp
      rubric_version.txt    ← which version of the rubric was used
```

The player layer (via the proxy) assembles the kid's view from these
files based on what they've unlocked. The agent reads and writes them
directly.

## The loop

- **Trigger.** Cron: once an hour while the server is up, or a schedule
  the operator controls. **Not per-request.** Completely decoupled from
  whether any kid is playing.
- **Budget per run.** 5–20 Claude calls depending on pass type. Evaluate
  is most expensive (reads the full concept canon), Iterate is cheapest
  (small targeted patches).
- **One concept + one pass per run.** Agent picks the next concept
  round-robin, weighted by "time since last touched" and "current
  quality score" (lower-scoring concepts get more attention).
- **No kid in the loop.** The agent runs whether anyone's playing or
  not. Quality compounds in the background.
- **Rate + cost cap.** Hard daily ceiling. Over budget → skip runs, log,
  alert.

## Safety & guardrails

The agent is autonomous; guardrails keep it honest.

- **Schema validation.** Every patch validates against the canon schema.
  Invalid → retry with error feedback, up to N times, then skip.
- **Contradiction check.** New entities cross-checked against
  `world.json`'s canonical list and contradiction_log. The agent must
  either respect existing canon or add to contradiction_log with an
  in-world resolution.
- **Reading-level gate.** All generated text runs through Dale-Chall (or
  equivalent). Fails → rewrite.
- **Tone filter.** A lightweight classifier pass for "scary / sad /
  preachy / off-brand for K-2." Fails → rewrite.
- **Diff size limit.** A single pass can't delete more than X% of canon
  or add more than Y new entities. Prevents thrashing and runaway
  growth.
- **Human review sampling.** Early on, every pass gets a human sanity
  check. Later: maybe 1 in 20. Never fully removed — always some
  sampling.
- **Cost cap.** Hard ceiling per day. Log and alert on approach, halt on
  breach.

## Starting state

Today's 5 concepts (electricity, ocean, volcano, dinosaurs, space) plus
their 11 authored extensions become each concept's **v0 seed**. We
convert `vignettes.json` entries into the per-concept directory
structure above. The agent starts by **Evaluating** each seed, writing
`quality.json`, and surfacing an improvement list. First Iterate passes
clean up the seed. First Generate passes fill in rubric-identified
gaps.

A new concept starts from just a concept name + a one-paragraph brief.
The agent runs a bootstrap Generate pass that produces a minimal v0
seed (one region, 2–3 NPCs, 2 affordances, 1 hidden, a world.json).
Then the standard loop takes over.

## Phase progression

Autonomy grows gradually. Each step de-risks the next.

- **v0 (today).** Flat `vignettes.json`. Hand-authored. No agent.
- **v1.** Canon restructured into per-concept directories. First agent
  stood up with **Evaluate pass only** — scores content, writes
  `quality.json`, surfaces a human-readable improvement list. **No
  autonomous writes yet.** Humans (Kevin or me) approve Iterate
  proposals manually. This proves the reading-level scorer, the tone
  filter, and the rubric's usefulness.
- **v2.** Agent autonomously runs Iterate on narrow templates ("rewrite
  this one sign at K-2"). Humans still gate Generate.
- **v3.** Agent runs Generate autonomously for low-risk entity types
  (hidden notes, signs). High-risk types (new NPCs, new sub-regions)
  still gated.
- **v4.** Full autonomous loop with rate + cost caps. Humans sample for
  quality periodically.

Human oversight never fully disappears. At minimum, periodic spot-check.

## Relationship to other plans

- **`GARDEN_PLAN.md`** — the *player experience* plan. Continues to
  describe what it feels like to explore the canon. The worldtender
  section is **retired** — the Designer Agent is the real authoring
  layer. Garden's affordance / hidden / thread / journal primitives are
  what the agent composes with.
- **`SUBSTRATE_PLAN.md`** — becomes the *shared storage* layer. The
  cross-kid accretion vision (kids' questions influence what exists in
  the canon) is a *future* feature where signal from play influences
  which concepts the agent prioritizes — but player questions never
  write canon directly.
- **`FACTORY_PLAN.md`** — retained as *architectural reference*.
  Schema/validator ideas apply, scoped per-concept rather than
  per-story. The asset-pipeline ideas apply later when we generate
  bespoke imagery.

## What makes this innovative, plainly

- The LLM is the **author**, not the reactor. Quality compounds.
- Every concept is a **living artifact** being polished by a patient
  designer.
- The **game gets better while nobody plays.**
- Teaching accumulates **across time, independent of any individual
  kid's engagement.**
- The explorer's experience of "this world seems to have more room every
  time I visit" is real — the room literally is being added between
  visits.

## Open questions

- **Canon persistence.** Git-versioned files (checked into repo) vs
  database vs both. Git gives clean history + rollback; a DB scales
  better. Start with git.
- **Rubric evolution.** Who updates the rubric? Humans for now. Later
  the agent could propose rubric changes that humans approve.
- **Agent style drift.** Over months, does the agent's voice drift from
  the original? Few-shot pinning in the system prompt + evaluate-
  against-canonical-examples should counter. Measure drift somehow.
- **Cross-concept awareness.** When the electricity agent writes a
  thread, does it know about ocean? Yes — each agent run includes a
  compressed summary of sibling concepts' canonical entities, just
  enough to spot thread opportunities.
- **Multiple voices.** A single agent producing everything might feel
  monotone. Later: multiple agents with slightly different prompt
  flavors (the Inventor Agent, the Natural-World Agent, the Story
  Agent) rotating within a concept.
- **Play-data feedback.** Should the agent ever learn from what kids
  actually do? "This affordance is never triggered; demote it." Out of
  scope for v1; flag as future.
- **First concrete v1 deliverable.** Probably: `canon/` restructure +
  an Evaluate-only agent + a human-readable quality report. Not writing
  to canon yet, just rating it.
