# Story Quest Factory — Shared Substrate Design

> Design notes for a collective, curiosity-gated world generation system.
> Captures a conversation about extending SQF beyond single-player generation
> into a shared substrate where every kid's questions enrich worlds for all.

---

## Core Concept

Every kid's questions contribute to a **collective world library**, but access
is gated by curiosity. Questions are both the key and the contribution.

- A central repository of generated content, organized by concept
  (electricity, rivers, bones, friendship, etc.)
- When Kid A asks about electricity, the LLM generates a "pass" — rooms, an
  NPC, a puzzle, a mini-game — stored keyed to the concept
- When Kid B asks about electricity later, the LLM doesn't start from
  scratch; it **extends** what exists: a new character who knows something
  the first NPC didn't, a puzzle that builds on the first one's mechanic, a
  room that connects two previously separate areas
- Over time, each concept becomes a rich, multi-layered region with genuine
  depth — not because any one kid went deep, but because cumulative asking
  built it up
- Each kid only sees the parts they've unlocked by asking. Their personal
  map is a subset of an ever-growing whole.

## Why This Is Interesting

- **Flips a cost constraint into a feature.** Per-kid generation budget stays
  the same, but world quality compounds. The 10th kid asking about
  electricity gets a much richer world than the first.
- **Soft curriculum without being didactic.** Popular concepts naturally
  become the deepest, most polished regions. Niche questions still get
  content but less of it — which is fine; the kid who asked a niche question
  gets a world custom-made for their weird interest.
- **Curiosity as currency.** A kid can't just wander into the electricity
  kingdom — they have to wonder about it first.

---

## Architecture: Two-Layer Model

Separate **the substrate** (shared, concept-keyed, ever-growing) from **the
player map** (personal, unlock-gated, a view over the substrate). Everything
in the player map is a reference into the substrate plus personal state.

```
substrate/
  concepts/
    electricity/
      canon.json        ← world bible for this concept
      rooms/            ← every room ever generated for electricity
      npcs/
      items/
      puzzles/
      minigames/
      dialogue/
      hooks/            ← open narrative threads awaiting extension
      contributions/    ← log of every generation pass
    magnetism/
    rivers/
    ...
  bridges/              ← cross-concept connections

players/
  kevin_kid_01/
    unlocked.json       ← what they've accessed from the substrate
    questions.json      ← their personal question history
    progress.json       ← flags, completed puzzles, relationships
    map.json            ← their personal world layout
```

---

## The Concept Canon File

The world bible for a concept. Fed into every generation prompt for that
concept. Must stay compact — it's going into context every time.

```json
{
  "concept_id": "electricity",
  "concept_aliases": ["lightning", "power", "sparks", "circuits"],
  "established_tone": "wonder with a hint of danger; electricity is alive-ish but not scary",
  "visual_motifs": ["copper wires as vines", "bulbs as fruit", "storm clouds"],
  "canonical_entities": {
    "npcs": [
      {"id": "npc_volta", "role": "elder scientist", "knows_about": ["circuits", "batteries"], "contradicts": ["npc_sparkle"]},
      {"id": "npc_sparkle", "role": "storm sprite", "knows_about": ["lightning", "weather"], "believes": "electricity is alive"}
    ],
    "landmarks": ["copper_grove", "bulb_orchard", "the_great_circuit"],
    "items_of_significance": ["the_first_battery", "sparkle_feather"]
  },
  "open_hooks": [
    {"id": "hook_042", "text": "What happens when lightning strikes the copper grove?", "created_from_question": "q_8831"},
    {"id": "hook_057", "text": "Volta mentions a lost apprentice", "status": "unresolved"}
  ],
  "contradiction_log": [
    {"topic": "is electricity alive?", "resolution": "two NPCs disagree; kid decides"}
  ],
  "generation_count": 14,
  "last_extended": "2026-04-19T10:22:00Z"
}
```

**`open_hooks` is doing critical work** — it's how each generation pass
leaves dangling threads for future passes to pick up. This is what makes the
world feel like it's growing rather than sprawling.

---

## Substrate Entities (Room/NPC/Puzzle)

Follow the existing SQF schema but add substrate-specific metadata:

```json
{
  "id": "room_elec_0043",
  "concept_id": "electricity",
  "name": "The Humming Vault",
  "description": "...",
  "connections": ["room_elec_0041", "room_elec_0058"],
  "contains_npcs": ["npc_volta"],
  "contains_items": ["item_spark_key"],
  "puzzles": ["puzzle_elec_0019"],

  "substrate_meta": {
    "created_in_pass": "gen_pass_0007",
    "seed_question_id": "q_8812",
    "seed_question_text": "how does a battery hold electricity?",
    "contributed_by_player": "anon_hash_4a9f",
    "extends_hooks": ["hook_031"],
    "creates_hooks": ["hook_042", "hook_043"],
    "semantic_embedding": [0.12, -0.44]
  }
}
```

The semantic embedding is how you detect whether a new question is asking
something already covered or something genuinely novel.

---

## Player's Unlocked View

```json
{
  "player_id": "kevin_kid_01",
  "unlocked_concepts": {
    "electricity": {
      "first_unlocked": "2026-04-15",
      "unlock_question": "why does my hair stick up?",
      "unlocked_rooms": ["room_elec_0043", "room_elec_0044", "room_elec_0058"],
      "unlocked_npcs": ["npc_volta"],
      "unlocked_items": ["item_spark_key"],
      "unlocked_puzzles": ["puzzle_elec_0019"],
      "visible_hooks": ["hook_042"],
      "not_yet_discovered": ["npc_sparkle", "room_elec_0041"]
    },
    "rivers": {}
  },
  "locked_concepts_teased": ["magnetism", "bones"]
}
```

`not_yet_discovered` powers the "locked door" hints — the kid can see there's
more, but needs to ask to open it.

---

## The Generation Pass — The Actual Loop

When a kid asks a question:

### 1. Classify the question
- **Concept match**: which concept(s) does this relate to?
- **Novelty score**: how semantically distant from existing content for that concept?
- **Contribution type**: does this warrant a full pass, a small addition, or just an NPC dialogue branch?

### 2. Decide the action — three tiers

- **Major pass** (novel concept or high-novelty question within existing
  concept): generate a new region — a few rooms, an NPC, a puzzle, new
  hooks. Expensive but rare.
- **Minor extension**: add one item, one dialogue branch, one mini-game to
  existing content. Cheap and common.
- **Hook resolution**: the question addresses an open hook — generate
  content that closes that thread.

### 3. Build the generation prompt
Feed the LLM:
- The concept's `canon.json`
- Compressed summary of recent additions
- List of `open_hooks`
- The `STYLE_GUIDE`
- The kid's question

Ask for output matching the existing SQF schema.

### 4. Validate and merge
- Schema validation
- Contradiction check against canon
- Update `canon.json` with new entities/hooks
- Log the contribution

### 5. Update the player's unlocked view
- Grant access to the new content
- Mark the question answered
- Potentially tease adjacent locked content

---

## The Bridges Layer

Cross-concept magic. Periodically (or when a question spans concepts), run a
pass that looks for link opportunities:

```json
{
  "bridge_id": "bridge_0003",
  "concepts": ["electricity", "magnetism"],
  "type": "shared_npc",
  "entity_id": "npc_faraday_cat",
  "narrative": "A cat who walks between the copper grove and the iron hills",
  "requires_unlock": ["electricity", "magnetism"]
}
```

The kid only encounters bridge content if they've unlocked both sides —
creating an "aha" moment when concepts connect.

---

## Novelty Detection with Embeddings

For each new question, embed it and compare against:
- The concept's existing question log
- The embeddings of existing substrate content

Three outcomes:

- **High similarity to existing content**: route the kid to existing content
  rather than triggering generation. Save the API call.
- **Medium novelty**: minor extension pass.
- **High novelty**: major pass, new hooks created.

This is the main cost-control lever and prevents the substrate from filling
up with near-duplicates.

---

## Canon Drift Prevention

Multiple mechanisms working together:

- Every generation prompt includes `canon.json` — LLM sees what's established
- Strict schema rejects malformed additions
- Periodic "canon review" passes where the LLM reads the full concept and
  flags contradictions or suggests reconciling content
- `contradiction_log` tracks known inconsistencies and their in-world
  resolutions, so future generations can reference them rather than
  pretending they don't exist

---

## Second-Order Design Ideas

- **Map as portrait of a kid's mind.** Each kid's accessible map is a visible
  record of what they've wondered about. Beautiful artifact for parents and
  the kid themselves later.
- **Social discovery without social interaction.** Kids never talk to each
  other but benefit from each other. An NPC might mention "the traveler who
  came before asked about storms" — warm collective presence without direct
  contact. Safer than multiplayer, richer than single-player.
- **Emergent canonical lore.** Over months, certain NPCs/items/places get
  asked about so much they become "famous" in the game universe. Surface
  this — a "most-visited" character, a legendary item. The world develops
  folklore shaped by aggregate curiosity.
- **Ghost-content as a feature.** Content a kid hasn't unlocked leaves hints
  — locked doors, mentioned-but-unvisited places, NPCs who reference friends
  the kid hasn't met. Creates pull toward new questions.
- **Parent/teacher seeding.** Let a trusted adult pre-seed questions to steer
  a kid toward topics they haven't asked about. Not forced lessons — planted
  curiosity.

---

## The Hardest Part

Making the LLM's extensions feel **coherent with prior extensions**. This is
essentially multi-author collaborative fiction where every author is the
same model at a different time with different context. Getting consistent
tone, avoiding stylistic drift, keeping characters recognizable across
passes — that's the real craft.

A `STYLE_GUIDE` and strict schema help, but a **world bible per concept**
(`canon.json`) that summarizes established canon and gets fed into every
generation prompt is what makes it work.

---

## Phase 0 Scope Recommendation

Smallest version that proves the loop:

- **One concept** (e.g., "forests" — Whispering Woods gives you seed content)
- The `canon.json` format
- One player's unlocked view
- Generation pass logic for **minor extensions only**
- No bridges, no cross-concept, no major passes yet

Get accretion working on a single concept with a single player asking
multiple questions. Watch whether extensions feel coherent over 10–20
passes. If they do, the hardest part is proven and everything else is
scaling it up.

---

## Open Questions to Resolve

- What's the compressed representation of current concept state that fits in
  context comfortably? (Summarization strategy for large concepts)
- Cost budget per question — what's the target API spend per kid per session?
- Storage backend — local-only (privacy) vs. shared server (collective
  accretion requires this); hybrid?
- Moderation of contributed content — even filtered kid questions can
  generate edge cases
- Embedding model choice — local (cheap, consistent) vs. API (higher quality)
- How are concepts bootstrapped? Manual taxonomy, or emergent from question
  clustering?

---

## Mapping to current code (2026-04-21)

Where the live runtime sits today vs. the substrate model:

| Substrate concept | Today's equivalent | Gap |
|---|---|---|
| `concepts/<id>/canon.json` | `vignettes.json` entry's `match` keywords | No canon. Vignette is monolithic. |
| Substrate entities (rooms/npcs/items) | `vignette.cast`, `vignette.set_pieces` | Not addressable by stable ID; not deduped across vignettes. |
| Player `unlocked.json` | `localStorage` save (Finn pos, met flags, spawnedRegions) | Records what was *spawned* in this player's world, not what was *unlocked* from a shared substrate. |
| Generation pass (major / minor / hook) | One-shot proxy call to library OR (eventually) Claude | Single tier. No accretion — re-asking deepens via a templated `subNpc`, not by extending canon. |
| `open_hooks` | `region.subNpcs` (flat templated lines) | No semantic hooks; sub-NPCs don't carry threads. |
| Novelty detection (embeddings) | Substring keyword match in `vignettes.json` | None. |
| Bridges layer | None | None. |

The current `vignettes.json` is the most embryonic possible substrate: one
concept = one canon = one vignette. To move toward the real model we need to
(1) split concept from content, (2) make entities addressable, (3) introduce
the three-tier generation pass.

## Phase 0a — single-concept accretion in the existing runtime

Smallest proof-of-loop that builds on what we already have. No new infra, no
embeddings yet, no per-player view (just localStorage). Concept: **electricity**.

1. **Restructure storage.**
   `world/substrate/concepts/electricity/canon.json` (the bible) +
   `world/substrate/concepts/electricity/passes/<id>.json` (each pass is one
   minor or major extension as a JSON blob in the existing vignette /
   set-piece schema). The proxy reads these instead of `vignettes.json`.
2. **Seed pass.** Convert today's Edison's-Workshop vignette into
   `passes/seed.json` plus a starter `canon.json` (entities = the 3 NPCs +
   the workbench/coil; one or two `open_hooks`).
3. **Major pass on first ask.** When a player asks an electricity-family
   question and has no electricity region yet, render `seed.json`. (Same
   visible behavior as today.)
4. **Minor extension on follow-up ask.** When the player asks another
   electricity-family question, the proxy returns one new entity — a single
   NPC + 1–3 set pieces — that *extends* the existing region rather than
   spawning a new chunk. Runtime: append to the live region (reuse the
   existing `deepenRegion` plumbing, but with rich content, not template
   stand-ins).
5. **Per-player unlocked view in localStorage.** Track which pass IDs this
   player has unlocked. On reload, replay each unlocked pass into the
   region.
6. **Hand-author the first 3–4 extension passes** before wiring the LLM, so
   the runtime + storage + accretion are validated independently of model
   quality.
7. **Then** swap the hand-authored passes for `claude-sonnet-4-6` calls that
   take `canon.json` + recent passes + the player's question and return one
   minor-extension pass.

Stop conditions for Phase 0a: the player can ask about electricity 4–5
times, each follow-up adds a coherent NPC or set piece to the existing
region, and reloading restores the accumulated state. Everything else
(major-pass-on-novel-concept, embeddings, bridges, parent seeding,
contribution log) is Phase 0b+.

## Phase 0b — second concept + cross-concept bridges

Once 0a holds, add a second concept (rivers or bones) and the first bridge
entity. Confirms the model generalizes.

## Phase 1 — multi-player substrate

Move concepts/ off the local filesystem to a shared store. Per-player
unlocked.json. Anonymous contribution log. This is where the "collective
substrate" thesis actually gets tested — does Kid B benefit from Kid A's
questions, and does it feel good?
