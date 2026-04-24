# Story Quest — Garden Plan

> Written 2026-04-22. Replaces the W5+ ambition in WORLD_PLAN.md and the
> "vignette as delivered tableau" framing of the existing runtime. Sits on
> top of SUBSTRATE_PLAN.md, which remains the storage model.

## The shift

Until now we've been building a **zoo of talking dioramas**. Kid asks a
question → a scene appears with 2–4 costumed NPCs → each NPC reads a
paragraph → kid leaves. The LLM, when wired, just writes bigger dioramas
faster. That's not exploration, and it doesn't delight — plaques never do.

The Garden is a different game. Teaching happens by **noticing**, not by
being told. The LLM's job stops being "write good dialogue" and becomes
"design a small world where a curious kid, left alone, can't help but
discover the idea." Dialogue shrinks. Environment grows. And the world
keeps moving when the kid isn't watching.

## Three commitments

1. **Teaching by noticing, not by telling.** NPCs gesture, invite,
   wonder aloud. They don't lecture. The *content* lives in what the
   environment lets the kid do, and what follows.
2. **Exploration that rewards looking carefully.** Every region hides
   things on purpose. Notes, items, a door that opens only when
   approached from a specific angle, a glint on a distant ridge. Not
   advertised. Found.
3. **A world that tends itself.** Between sessions, a worldtender
   process makes small changes. The kid logs back in and *something is
   different*. Mystery, ambient presence.

## Design pillars

### 1. Affordances over exposition
Each region ships 3–5 **interactive things**: a lever, a bell, a steaming
vent the kid can stand over, a pedestal that wants an item, a seed that
grows when watered, a switch that changes the light. NPCs point at them
("what do you think happens if you…?"). The *doing* is the teaching.

### 2. Hidden discoveries
Each region seeds 2–4 findable things with no dialogue hint: a crumpled
note wedged behind a boulder, a glinting crystal on a high shelf, a small
cave mouth behind a tree, an object half-buried at the terrain edge.
Discovering one adds a line to the journal and usually opens a thread.

### 3. Inventory & cross-region combinatorics
The kid carries a small bag. Items picked up in one region can be given
or used in another. Copper wire from Patti's workshop → shown to the
anglerfish in the deep → she lights up, reveals something about electric
eels. This is what makes the world feel like a world and not a library.

### 4. Vocabulary surface
Labeled props, signs, readable notes, hoverable NPC titles. Everything
the kid reads gets auto-logged in the journal's word list. Over weeks
the journal becomes a portrait of what they've learned to read and the
domains they've wandered into.

### 5. Journal
A simple overlay. Tap the book icon to open. Shows:
- **Places visited** (named regions, with screenshot thumbs if cheap)
- **Friends met** (NPCs, with the role_short as a caption)
- **Things in my bag** (inventory)
- **Words I learned** (auto-extracted from readable content the kid
  actually encountered)
- **Open mysteries** (unresolved hooks — "Volta mentioned a lost
  apprentice…")

The journal is the kid's *trace* of their own curiosity. Parents can
look at it and see what the kid has been wondering about.

### 6. Threads (the "aha" layer)
A thread is a conditional reaction. "If the kid picked up the
spark-crystal in Edison's workshop, Zira the storm sprite has a new line
about electric eels." LLM-authorable; worldtender-evaluable. Threads
don't announce themselves — the kid just notices that Zira said
something different this time.

### 7. The worldtender
An offline process that makes small changes to world state when the kid
isn't playing. Runs at session-start if ≥ N hours since last session
(single-player local doesn't need continuous uptime). Each tend makes
1–3 small, authored-feeling changes — drawn from a menu of templates
plus occasional LLM-composed novelties:

- An NPC has drifted to a neighboring region for the day
- A new note has been pinned to a tree
- Weather has changed (fog, rain, dawn light)
- An item has moved
- A new path has worn itself into the grass between two spots the kid
  visited a lot
- A locked door is now unlocked
- A stranger has set up a tent

The worldtender is the long-arc magic. It's how the garden grows.

## The LLM's new job

The LLM is a **level designer**, not a dialogue writer. It composes
scenes whose *mechanics* teach. The output schema shifts accordingly:

```
{
  "concept_id": "electricity",
  "region_name": "Edison's Workshop",
  "family": "earthen",
  "terrain": [...],          // existing
  "set_pieces": [...],        // existing
  "cast": [                  // still authored, but briefer, invitational
    {
      "name": "Thomas Edison",
      "appearance": {...},
      "gestures": [
        "the switch on the bench is asking to be flipped",
        "that bulb will tell you a story if you give it a second"
      ]
    }
  ],
  "affordances": [           // NEW — interactive primitives
    {
      "id": "coil_lever",
      "kind": "lever",
      "position": {...},
      "label": "coil switch",
      "effects": [
        { "on": "pull", "plays": "sfx.coil_hum", "sets_flag": "coil_humming", "reveals": "affordance:bulb_pedestal" }
      ]
    },
    ...
  ],
  "hidden": [                // NEW — unadvertised findables
    {
      "id": "volta_note",
      "kind": "note",
      "position": {...},
      "reveal_condition": "proximity < 1.5m",
      "text": "tried the zinc-copper stack again — THIS time it held a charge for a whole minute! — T.E.",
      "grants_item": null
    }
  ],
  "threads": [               // NEW — conditional reactions
    {
      "id": "thread_eels",
      "requires_flags": ["picked_up:spark_crystal"],
      "unlocks_dialogue": { "npc": "Zira", "line": "electric fish use the same trick…" }
    }
  ]
}
```

Dialogue is now 2–3 lines per NPC, not 5. Most teaching moves into the
environment.

## What we keep from today's runtime

- Chunk-based spawning, terrain ops, set pieces, chibi humanoid + costume
  system, save/restore, proxy (library + live modes). All solid
  substrate.
- The concept-keyed vignettes.json structure — but the content inside each
  vignette shifts from "delivered text" to "designed space."

## What changes

- **Vignette schema.** Add `affordances`, `hidden`, `threads` fields.
  `cast` dialogue shrinks to gestural lines.
- **Rendering.** Interactive objects with tap/E-to-interact. Proximity
  triggers for hidden reveals. World-state flags.
- **Save format.** Add `inventory`, `journal`, `worldFlags`,
  `threadsResolved`.
- **NPCs.** Short gestural speech; most dialogue gated behind threads.

## What's new

- Affordance primitives library (lever, bell, pedestal, steam-vent,
  lit-panel, planter, combine-slot, pickup-shelf, …)
- Inventory system (bag with ~8 slots)
- Journal UI
- Thread / flag evaluator
- `tender.py` — the worldtender process
- Hidden-discovery mechanic (glint rendering, proximity reveal, log)

## Smallest first step — Phase G0

Prove the shape on ONE region, end to end. Ship the feeling, not the
scale.

**Region:** Edison's Workshop (already authored).
**New ingredients:**
- 3 affordances
  - `coil_lever`: pull to start/stop the Tesla coil humming (sound + a
    visible electric-arc sprite on the coil)
  - `bulb_switch`: flip to light the hanging bulbs (all bulbs go from
    dim to bright; sets a flag so dialogue changes)
  - `material_pedestal`: a pedestal that accepts an item; metal from
    the bag makes it glow, rubber makes it stay dark (teaches
    conductor/insulator without a lecture)
- 2 hidden discoveries
  - `volta_note`: a crumpled paper tucked behind Edison's anvil — text
    quoted above. Found by walking close.
  - `spark_crystal`: on a high shelf, visible as a glint from across
    the region. Pickup → goes in bag.
- 1 thread
  - `thread_eels`: if `picked_up:spark_crystal`, the *next* time the
    kid asks about ocean (first visit or re-visit), the anglerfish has
    a new branch: "I know this light. My cousin the electric eel taught
    me."
- Basic journal overlay (open with a book icon) showing regions visited
  + bag contents.

**Out of scope for G0:** worldtender, seasons, time, cross-kid
substrate. Those come after the loop feels good on one region.

**Definition of done:** a kid who has never played before walks to the
workshop, notices the switches, flips them (coil hums, bulbs light), sees
the glint on the shelf, walks over, picks up the crystal, journal ticks.
Later asks about ocean, meets the anglerfish with the new line. Delight:
*the world noticed what I did*.

## Where this sits relative to prior plans

- **WORLD_PLAN.md** W5+ (LLM-authored vignettes, validator, repair
  loop) — superseded by this direction. Dialogue-factory thinking
  retired.
- **SUBSTRATE_PLAN.md** — still the storage model. Concepts, canon,
  accretion, cross-kid contribution. The worldtender will operate on the
  substrate. The Garden is the **experience model** built on top.
- **FACTORY_PLAN.md** — retained architecturally. The schema/validator
  ideas still apply; the schema itself changes per above.

## Decisions locked 2026-04-22

- **Interaction model (tablet, 9yo).** Tap the object → Finn
  auto-walks to it → a small contextual prompt appears near the object
  ("pull lever" / "read note" / "pick up") → second tap confirms.
  Respects agency (you *chose* to interact), impossible to trigger
  accidentally, gives a beat to change your mind. Same pattern as A
  Short Hike / modern mobile adventures.
- **Journal presentation.** A physical in-world notebook Finn
  carries. Tap the book icon (bottom-right of the HUD) → it flips open
  into an overlay with tabbed pages (**Places / Friends / Bag / Words
  / Mysteries**). Reinforces "this is *your* record" better than a flat
  menu, and the tab structure scales cleanly as we add new kinds of
  entries.
- **Item consumption.** **Always recoverable.** Items placed in
  affordances stay in the bag. Wrong slot ≠ lost item. At 9 the lesson
  we want is "curiosity costs nothing." Weight + consequence come from
  what the kid *notices*, not what they *lose*. Where a choice needs to
  feel meaningful, gate it behind a thread, not behind item loss.
- **Worldtender first move.** A new NPC wanders between regions
  overnight, leaving a footprint trail the kid can follow. The NPC is
  somewhere new when they log back in — maybe the stranger is leaning
  against the Tesla coil, maybe perched on the volcano lookout. Short,
  warm, "world noticed you were gone" moment. This is the template to
  prototype first once G0 is in.

## Still open

- What's the ratio of NPC dialogue to environmental teaching? G0 guess:
  30/70. Tune after play-testing.
- Should the kid be able to drop items (not just use them)? Probably
  yes — creates accidental tender fodder ("someone left a feather
  here").
- Worldtender change-template menu. Besides the wandering-NPC
  template above: new note pinned, weather change, path worn between
  frequented spots, locked door now open, stranger's tent. Which ones
  make the cut?
- Journal readability / vocab tracking. Auto-extract vocab from
  *signs* the kid walked close enough to read — not from spoken
  dialogue. Signs become the vocab surface on purpose. Needs a
  sign-primitive in the affordance library.
