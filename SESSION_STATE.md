# Session State — 2026-04-21 (late)

## TOMORROW START HERE — broken: outfit primitives floating off the NPC

A screenshot from the user shows Dr. Kai's wide-brim hat + lab coat hanging in the air with no character under them. The outfit pieces are added to the npcGroup at hardcoded local-y positions (1.95 for hats, 1.28 for collars) tuned for a knight/wren-sized character — but `setupKayKitChar` calls `groupTarget.remove(groupTarget.children[0])` to wipe before adding the GLB (line ~2584), and the GLB's pivot may not be at feet=0. Also: `MODEL_HEAD_Y` is currently a constant assumption; it doesn't account for character GLBs of different actual heights, scale variants, or the chunk-relative y of the npcGroup.

Concrete debug steps:
1. Open browser console while spawning the volcano vignette. Inspect the npcGroup of Dr. Kai — print `group.position` and walk children, log each `child.position.y` and `child.name`.
2. Confirm whether the GLB's bounding box origin is at feet (y=0) or somewhere else. If it's offset, `_attachOutfit` must compensate — easiest fix is to compute the GLB bbox after load and store a per-model `headY` reference.
3. Apply `look.scale` to the outfit group too. A scale-0.7 child shouldn't have a scale-1.0 hat.
4. Likely fix: in `_attachOutfit`, scale the returned group to match `look.scale` and shift its y so the head reference matches the model's actual head position.

Until that's fixed, today's costume work is mostly invisible / weird in-game even though all the code paths exercise correctly.

---


Brief for picking up this project cold. For full context read `WORLD_PLAN.md` and `FACTORY_PLAN.md`, then **`SUBSTRATE_PLAN.md` (the new north star — supersedes the W5+ section of WORLD_PLAN)**. The latest commit on `main` is the authoritative source; this doc summarizes the shape of the live codebase.

## Where we are

**W4 complete. W5 partial — multi-NPC vignette rendering shipped today (library-driven, hand-authored, 5 starter topics with set-piece props). Plan pivoted to the substrate model — see `SUBSTRATE_PLAN.md`. Current code is the embryonic version: one concept = one flat vignette. Next: Phase 0a (single-concept accretion with hand-authored extension passes).**

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
- Dynamic chunks are 50×50 at 8 fixed docks around chunk 0 (cardinal + diagonal at distance 125). The 10-unit gap between home and each dock is spanned by a walkable stone-slab bridge (see Bridges below); impassable outside chunks AND outside bridges.
- `pickFreeChunkDock()` returns the next unclaimed dock.

### Bridges (walkable connectors)
- `bridges[]` — oriented-rectangle registry. Each entry has `cx, cz, halfLen, halfWid, cos, sin, y, chunkId, mesh`.
- `findBridgeAt(x, z)` does rotated-rect containment. `isBlocked` falls through to it when off-chunk; `heightAt` returns `bridge.y` on-bridge so Finn walks a flat path.
- `buildBridgeForChunk(chunk)` creates the stone slab mesh (BoxGeometry) at the midpoint between home's nearest edge/corner and the chunk's nearest edge/corner. Cardinal docks get halfLen=6 slabs; diagonals get halfLen=9 slabs at ±π/4. Slab top aligns with `bridge.y` (which is natural noise height + 0.15 rise) so the path reads as raised stone.
- Created in `spawnRegion` right after `buildChunkMesh(newChunk)` (visible during drop-in; chunk tweens up to meet it), and in the restore-path dressing loop.

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

## Phased roadmap (W0–W6 + substrate)

- **W0** ✓ — 3D shell
- **W1** ✓ — Terrain + prop kit (Quaternius + KayKit) + biomes
- **W2** ✓ — Hand-authored Whispering Woods vignette (Counting Bridge puzzle, four-beat climax)
- **W3** ✓ — Region registry + templates (crossing, lookout/mound, cliff, basin)
- **W4** ✓ — Campfire ask UX, topic dispatch, Map view, chunk-based world growth, fast-travel
- **W4 polish** ✓ — Per-family ground cover, family-specific GLB props, walkable bridges
- **W5 (in progress)** — LLM-authored vignettes. Today's slice: Python proxy (`llm_proxy.py`) with library / live / auto modes; hand-authored `vignettes.json` library (5 topics: electricity, ocean, volcano, dinosaurs, space) with rich set pieces; multi-NPC scene builder (`buildMultiNpcScene`) that places 2–4 cast members per chunk with per-character dialogue + appearance-hint character GLBs; engine-primitive set pieces (`glow_orb`, `pillar`, `slab`, `pool`, `mound`, `crystal`, `flag`) so each topic visibly furnishes its scene. Live Claude path is wired but needs a working `ANTHROPIC_API_KEY`; library mode is the active workflow.
- **W5 → substrate pivot** — Plan reshaped per `SUBSTRATE_PLAN.md`. Instead of one-shot vignettes per topic, every question contributes to a per-concept canon that future questions extend. Three-tier generation (major / minor / hook resolution). Per-player unlocked view over a shared substrate.
- **Phase 0a** (next) — Single-concept accretion. Convert today's flat `vignettes.json` into `world/substrate/concepts/<id>/canon.json` + `passes/*.json`. Hand-author 3–4 follow-up extension passes for electricity. Wire minor-extension on follow-up question (extends the existing region instead of spawning a new chunk). Per-player unlocked-pass tracking in localStorage.
- **Phase 0b** — Second concept + first cross-concept bridge.
- **Phase 1** — Multi-player substrate (move concepts/ off local fs).
- **W6** — Tablet polish, bundle, audio, multi-chunk UX (parallel track).

## Known open items (carry forward)

- **Map view doesn't draw bridges** — they're walkable but invisible on the minimap, so the "path between islands" story is only readable from world view. Easy follow-up: draw a thin line on the Map for each bridge.
- **W5 substrate pivot — current code is the embryonic version.** `vignettes.json` is one-vignette-per-topic; the substrate model wants concept-keyed canon + accumulating passes. Phase 0a in `SUBSTRATE_PLAN.md` is the smallest concrete step.
- **No working `ANTHROPIC_API_KEY` yet.** Live Claude path in `llm_proxy.py` is built but unproven — it 401'd on the user's last attempt. Library mode (the default fallback) doesn't need a key and works today.
- **All docks full at 8 chunks** — second ring / chunk removal not yet handled. Warn + no-op currently.
- **Ambient audio disabled** — flat pink noise read as airplane drone. Infrastructure kept; needs better source (wind gusts, per-biome loops).
- **Procedural dialogue is flat** — synthesized lines are templated stand-ins until W5 LLM integration.
- **Portrait phone dialogue panel crowds the count puzzle** — known; not blocking.

## File layout

- `SUBSTRATE_PLAN.md` — **the new north star.** Shared, concept-keyed, ever-growing world library; per-player unlock-gated view; three-tier generation. Read this first when picking up W5+.
- `WORLD_PLAN.md` — active vision + phased roadmap. The W5+ section is now superseded by SUBSTRATE_PLAN.
- `FACTORY_PLAN.md` — retained architecture reference (Schema v0.1, validator, asset pipeline). Still relevant — informs the substrate's per-entity schemas.
- `SPEC.md` — original Story Quest Episode 1 spec (historical)
- `world/index.html` — live 3D runtime (~2900 lines, self-contained). Includes today's W5 multi-NPC + set-piece rendering.
- `world/llm_proxy.py` — vignette proxy. Modes: `library` (default fallback, reads `vignettes.json`), `live` (calls Claude with cached system prompt), `auto` (library first, Claude on miss).
- `world/vignettes.json` — current substrate stand-in. 5 entries (electricity / ocean / volcano / dinosaurs / space), each with cast + set_pieces. Re-read on every request — hand-edit live.
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

Run `git log --oneline -5` for current. Evening polish run (in order):
1. `W4-polish: per-family ground cover for spawned chunks` — FAMILY_SKIN + dressChunkGroundCover.
2. `W4-polish: family-specific GLB props on spawned chunks` — FAMILY_SKIN.props + loadGLBOnce + dressChunkProps.
3. `W4-polish: walkable connector bridges between home and chunks` — bridges[] registry, isBlocked/heightAt patches, buildBridgeForChunk.
