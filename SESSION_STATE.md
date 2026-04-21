# Session State — 2026-04-20

Brief for picking up this project cold. For full context read `WORLD_PLAN.md` then `FACTORY_PLAN.md`. The latest commit on `main` is the authoritative source; this doc summarizes the shape of the live codebase.

## Where we are

**W4 complete. W5 (LLM-authored vignettes) is next.**

The whole interactive loop is in place end-to-end: Leo walks up to a campfire, asks a question (via topic button or text input), a new terrain chunk drops in adjacent to the home prairie with a hill-shaped region on it, an NPC appears on top with flavor dialogue. Follow-up questions on the same topic add sub-NPCs to the existing region. The world accumulates with each question. Save/resume persists across reloads.

## What's locked (from WORLD_PLAN and refined in practice)

- **Vision:** Leo walks up to a campfire, asks a question, a themed region spawns in a continuous 3D world he explores. World accumulates.
- **Visual style:** Stylized low-poly / toon (A Short Hike aesthetic). KayKit Adventurers + Quaternius kits.
- **Tech:** Three.js via importmap (no build step). Tablet-first. Self-contained HTML.
- **Two views:** third-person follow for walking, pulled-back Map view for the whole world. Fast-travel via Map tap (W4d-3).
- **Cast:** Finn (KayKit Rogue_Hooded), Wren (Mage), Pip (bipedal chibi frog). All idle/walk animated; Wren + Pip follow Finn. Bridge Keeper (Knight) + dynamic NPCs for spawned regions.
- **Vignette model:** implicit teaching, layered depth (follow-up questions deepen via sub-NPCs), four-beat climax (Whispering Woods is the reference).

## Live architecture

### Chunks (W4d)
- World is a collection of chunks in `chunks[]`. Each has `offset`, `size`, `segments`, `geometry`, `mesh`, `biome`, `palette`, `groundColors`.
- `findChunkAt(x, z)` + `isBlocked(x, z)` route through the registry. Anywhere outside every chunk is impassable.
- `buildChunkMesh(chunk)` generates a chunk's terrain mesh with vertex-color palette baked in. Used for chunk 0 at load and for every spawned chunk.
- Chunk 0 is the home prairie (180×180 at origin). Contains the campfire, Whispering Woods bridge vignette, Quiet Overlook.
- Dynamic chunks are 50×50 at 8 fixed docks around chunk 0 (cardinal + diagonal at distance 125). 10-unit impassable gap between home and each dock.
- `pickFreeChunkDock()` returns the next unclaimed dock.

### Regions + templates
- `regions[]` registry, each with `template`, `center`, `params`, `topic`, `topicKey`, `family`, `subNpcs`, `chunkId`.
- Templates:
  - `TEMPLATE_CROSSING`: hardcoded for Whispering Woods (ravine + bridge + planks + counting puzzle + four-beat climax).
  - `TEMPLATE_MOUND`: gentle bell-shaped hill (TEMPLATE_LOOKOUT is an alias).
  - `TEMPLATE_CLIFF`: sharp rise with flat plateau (for earthen / airy topics).
  - `TEMPLATE_BASIN`: shallow carve (for watery topics).
- Each template has `terrainDelta(x, z, region)` + optional `snapOut` + `build(region, saved)`.
- Shared `buildDynamicNpcScene` is used by MOUND/CLIFF/BASIN — places an NPC on top (BASIN puts it on the north rim instead of in the carve).

### Topic dispatcher
- `resolveTopicFamily(topicString)` keyword-matches into earthen / watery / wooded / airy / default.
- `FAMILY_CONFIGS` picks template + params per family (earthen → CLIFF, watery → BASIN, wooded/default → MOUND, airy → tall CLIFF).
- `FAMILY_SKIN` overrides ground palette + grass/pebble colors + scatter density per family — merged over `biome` via `makeChunkBiome(family)` so every spawned chunk's terrain color AND ground cover reflects its topic.
- `FAMILY_NAMES` is a per-family name pool for synthesized NPCs.
- `resolveTopic(topicString)` returns `{ family, template, params, content: { name, npcName, lines } }`.

### Per-chunk ground cover
- `dressChunkGroundCover(chunk, region)` scatters grass/flowers/pebbles inside a single chunk using per-family materials (cached in `familyGroundMats`) and a deterministic per-chunk RNG seeded from the chunk's offset — so save/restore reproduces the same layout without persisting positions.
- Skips `isBlocked(x, z)` cells (basin carves, cliff walls) and a clearance circle of `params.radius + 1` around the region center so the NPC isn't buried.
- Called from `spawnRegion`'s drop-in tween complete callback, and from a restore-time pass after the scatter helpers are defined (ordering matters — helpers close over `grassTuftMat`/`pebbleMat`).
- Home chunk still uses the original module-level `scatter()` + shared materials.

### Spawn flow
- `spawnRegion(topicString)`:
  1. Normalize topic, check for exact match with an existing region's `topicKey` → if match, `deepenRegion` (adds a sub-NPC beside it).
  2. Otherwise resolve the topic, pick a free chunk dock, create a new chunk + region, push both, call `buildChunkMesh(newChunk)`.
  3. Animate chunk drop-in (tween `mesh.position.y` from -8 to 0 over 1.4s).
  4. On tween complete, call `region.template.build(region, null)` to place NPC.
  5. Call `updateWorldCameraBounds()` so Map view fits the new chunk.
  6. `saveState()` persists.

### Dialogue system
- Campfire script has both choice buttons (Volcanoes / Ocean / Forest) and a text input (`input: { placeholder, submitText, spawnFromInput, goto }`).
- Reusable NPCs (campfire) disarm on end and rearm only after Finn leaves their promptDist.
- Dialogue camera frames Finn + NPC side-on during conversation.

### Audio (procedural)
- `audio` object — pink-noise ambient (currently disabled; "airplane drone" feel), plus: per-speaker dialogue blip, puzzle-chime arpeggio, bandpass-sweep whoosh (climax), filtered-noise footsteps.
- Init on first `pointerdown` (iOS gesture requirement).

### Save / resume (localStorage)
- `saveState()` serializes: Finn position + facing, flags bag, per-NPC `met`, spawnedRegions (with `chunkId`, `templateId`, `family`, `subNpcs`, `topic`, etc.).
- `savedState = loadSavedState()` runs at module load. Spawned regions + chunks restore into `regions[]` and `chunks[]` synchronously; each restored chunk's mesh builds right after chunk 0's.
- Save triggers: end of dialogue, climax beat 4, periodic 2s while walking, after each spawn.
- **Reset** button in top-right HUD clears save + reloads.

## Phased roadmap (W0–W6)

- **W0** ✓ — 3D shell
- **W1** ✓ — Terrain + prop kit (Quaternius + KayKit) + biomes
- **W2** ✓ — Hand-authored Whispering Woods vignette (Counting Bridge puzzle, four-beat climax)
- **W3** ✓ — Region registry + templates (crossing, lookout/mound, cliff, basin)
- **W4** ✓ — Campfire ask UX, topic dispatch, Map view, chunk-based world growth, fast-travel
- **W5** — LLM-authored vignettes (author layer, validator, repair loop). Currently `resolveTopic` synthesizes flat dialogue; W5 replaces it with a structured LLM blueprint. Needs local Ollama/llama.cpp.
- **W6** — Polish: tablet performance, save/resume polish, bundle, improved multi-chunk UX

## Known open items (carry forward)

- **No biome GLB props on spawned chunks** — procedural grass/flowers/pebbles are in (family-tinted), but Quaternius trees/bushes/rocks still only scatter on the home prairie. Next polish step could fan those across dynamic chunks with family-specific prop lists (oak/birch for wooded, boulders for earthen, etc.).
- **Impassable gap between chunks** — fast-travel via Map bridges this for now. W4d-4+ could add walkable connectors (bridges, portals) or a seamless transition.
- **All docks full at 8 chunks** — second ring / chunk removal not yet handled. Warn + no-op currently.
- **Ambient audio disabled** — flat pink noise read as airplane drone. Infrastructure kept; needs better source (wind gusts, per-biome loops).
- **Procedural dialogue is flat** — synthesized lines are templated stand-ins until W5 LLM integration.
- **Portrait phone dialogue panel crowds the count puzzle** — known; not blocking.

## File layout

- `WORLD_PLAN.md` — active vision + phased roadmap
- `FACTORY_PLAN.md` — retained architecture reference
- `SPEC.md` — original Story Quest Episode 1 spec (historical)
- `world/index.html` — live 3D runtime (~2570 lines, self-contained)
- `world/assets/` — Quaternius + KayKit GLBs (CC0)
- `engine/`, `schema/`, `validator/` — Phase 0 2D engine / schema / validator (background reference, will be retired)
- `index.html` — original Story Quest 2D game
- `archive/` — superseded plans

## How to resume

1. `cd /Users/kevinbolander/clawd/projects/story-quest && git pull`
2. Serve: `cd world && python3 -m http.server 3458 --bind 0.0.0.0` → `http://brick.local:3458/`
3. Check the latest commits: `git log --oneline -10`
4. Read `WORLD_PLAN.md` if touching direction; this doc for live state.
5. Decide next phase:
   - W5 (LLM vignettes) if continuing the plan. Substantial: needs Ollama + prompts + validator + repair loop.
   - Polish pass: ground cover for dynamic chunks, walkable chunk connectors, better ambient audio, LLM or heuristic-driven dialogue enrichment.

## Latest commit

Run `git log --oneline -1` for current. Recent work: W4-polish — per-family ground cover (FAMILY_SKIN) so spawned chunks' terrain + scatter colors reflect the topic.
