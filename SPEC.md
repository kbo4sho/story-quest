# Story Quest — Episode 1 Prototype Spec

## Overview
A canvas-based, tablet-first interactive story game for K-2 kids. One complete episode with 5 scenes mixing learning challenges, story branches, and play moments. Runs in mobile Safari/Chrome on a tablet.

## Tech Stack
- **Single HTML file** (self-contained, no build step)
- HTML + CSS + vanilla JS
- CSS animations for transitions and effects
- Touch-first interactions (tap, drag)
- Inline SVG or CSS art for characters/environments (no external image dependencies for prototype)
- Audio: optional SFX via Web Audio API (stretch goal)

## Visual Style
- Bright, warm colors — greens, golds, purples, sky blues
- Storybook aesthetic — soft edges, slight paper texture feel via CSS
- Large touch targets (minimum 48px, prefer 64px+)
- Big readable text (24-32px base)
- Character illustrations: simple, expressive, CSS/SVG-based for prototype
- Scene transitions: fade or slide

## Characters
- **Finn** — brave explorer kid (green hat, adventurous)
- **Wren** — curious reader girl (purple cloak, book)
- **Pip** — friendly frog companion (comic relief, hints)

## Episode 1: "The Whispering Woods"

### Scene 1: The Hatch Opens (Narrative Setup)
- **Type:** Story introduction
- **Visual:** A golden hatch glowing in a grassy meadow. It creaks open.
- **Narrative:** "Deep in a meadow where wildflowers hum, a golden hatch begins to glow..."
- **Interaction:** Tap the hatch to open it → Finn climbs out, looks around
- **Transition:** Wren and Pip follow. "Where are we?" Wren asks, opening her book.
- **Choice:** "Pip hears something in the woods. Should we follow the sound?"
  - **Go toward the sound** → Scene 2A (river path)
  - **Explore the meadow first** → Scene 2B (meadow discovery, then river path)

### Scene 2A: The Counting Bridge (Learning Node — Math)
- **Type:** Learning challenge
- **Visual:** A wooden bridge with missing planks. River below. Friendly troll character.
- **Narrative:** "The bridge is broken! The Bridge Keeper needs help counting the planks to fix it."
- **Challenge:** Count objects / simple addition
  - **Easy (K):** "How many planks do you see?" (count 1-10 with visual objects)
  - **Medium (1st):** "We need 10 planks but only have 6. How many more?" (addition/subtraction within 10)
  - **Hard (2nd):** "Each side needs the same number. We have 14 planks for 2 sides." (intro division/fair sharing)
- **Interaction:** Drag planks into place / tap the correct number
- **Success:** Bridge rebuilds with sparkle animation. "You did it!" Troll waves them across.
- **Adaptive:** Start at Medium. If wrong twice → drop to Easy. If right first try → next challenge bumps to Hard.

### Scene 2B: Meadow Discovery (Play Moment + Story)
- **Type:** Play/exploration
- **Visual:** Colorful meadow with interactive elements (flowers, butterflies, a peculiar stone)
- **Interaction:** Tap things to discover them. Collect 3 "wonder items" (a feather, a shiny stone, a flower)
- **Narrative:** Each item Pip comments on. "Ooh, shiny! Pip likes shiny!"
- **Transition:** After collecting 3 items → "I hear water! Let's go!" → Scene 2A

### Scene 3: The Word Forest (Learning Node — Phonics/Reading)
- **Type:** Learning challenge
- **Visual:** Trees with letters/words hanging from branches like fruit. Owl character perched above.
- **Narrative:** "The Word Owl guards the path. Only those who can read the forest signs may pass!"
- **Challenge:** Letter/word recognition
  - **Easy (K):** Match uppercase to lowercase letters (tap pairs)
  - **Medium (1st):** Sound out CVC words — tap the picture that matches the word (cat, dog, sun, hat)
  - **Hard (2nd):** Read a short sentence, pick the picture that matches
- **Interaction:** Tap to select, drag to match
- **Success:** Trees part to reveal the path. Owl hoots approvingly.

### Scene 4: The Crystal Cave (Story Branch + Play)
- **Type:** Story choice + customization
- **Visual:** Glittering cave interior. Crystals in different colors. A mysterious door with a symbol.
- **Narrative:** "The cave is full of crystals! Each one glows a different color..."
- **Play moment:** Tap crystals to hear them chime (different tones). Pick your favorite color → it becomes your "quest crystal" (shows in UI for rest of episode)
- **Story choice:** The door has three symbols:
  - ⭐ Star → "The Brave Path" (action-oriented finale)
  - 📖 Book → "The Wise Path" (puzzle-oriented finale)  
  - 🌿 Leaf → "The Nature Path" (discovery-oriented finale)
- **Transition:** Door opens to reveal Scene 5 variant

### Scene 5: The Second Hatch (Finale + Cliffhanger)
- **Type:** Final challenge + story resolution
- **Visual:** A clearing with another golden hatch. But it's locked! A final challenge stands between them and the exit.
- **Challenge (varies by Scene 4 choice):**
  - ⭐ **Brave Path:** Pattern completion — "The lock needs the right sequence!" (shape/color patterns, 3-5 items)
  - 📖 **Wise Path:** Story sequencing — "Put these events in order to unlock the hatch!" (3-4 picture cards from the episode)
  - 🌿 **Nature Path:** Sorting — "The lock needs the right nature items!" (sort animals vs plants, or living vs nonliving)
- **Success:** Hatch glows and opens. Celebration animation (sparkles, confetti, characters cheer).
- **Narrative:** "The hatch opens! But wait — Pip sees something through the hatch... a desert of golden sand stretching to the horizon. What adventures wait in the Sunstone Desert?"
- **Cliffhanger:** Brief glimpse of next episode's world. "To be continued..."
- **End screen:** 
  - ⭐ Stars earned (1-3 based on challenge performance)
  - 🔮 Quest crystal collected
  - 📊 "You solved X challenges today!"
  - "Come back tomorrow for Episode 2!"

## UI Elements

### Top Bar
- Episode title: "The Whispering Woods"
- Quest crystal slot (empty until Scene 4)
- Scene progress dots (5 dots, filling as you go)

### Narrative Text
- Bottom third of screen
- Large, readable font (Baloo 2 or similar rounded friendly font)
- Text appears word-by-word with subtle animation
- Tap to complete / advance

### Choice Buttons
- Large rounded rectangles
- Icon + text
- Slight bounce animation on appear
- Glow on touch

### Learning Challenges
- Center stage with clear visual instruction
- Drag targets have generous hit areas
- Correct: green pulse + stars + happy sound
- Incorrect: gentle shake + "try again!" (no punishment, encouraging)
- Pip gives hints after 2 wrong attempts

## Adaptive Difficulty System
```
difficulty_level = 1  (0=Easy/K, 1=Medium/1st, 2=Hard/2nd)

on_correct_first_try:
  streak += 1
  if streak >= 2: difficulty_level = min(2, difficulty_level + 1)

on_incorrect:
  streak = 0
  attempts += 1
  if attempts >= 2: difficulty_level = max(0, difficulty_level - 1)
  show_hint()
```

## State Management
```javascript
const gameState = {
  currentScene: 1,
  difficulty: 1,        // 0=K, 1=1st, 2=2nd
  streak: 0,
  stars: 0,
  questCrystal: null,   // color chosen in Scene 4
  chosenPath: null,      // star/book/leaf from Scene 4
  meadowVisited: false,  // Scene 2B
  wonderItems: [],       // collected in meadow
  totalCorrect: 0,
  totalAttempts: 0,
}
```

## Responsive Layout
- **Target:** iPad (768x1024 and up)
- **Orientation:** Landscape preferred, portrait supported
- **Min width:** 320px (phone fallback)
- **Max content width:** 1200px, centered
- CSS Grid for scene layout
- `viewport` meta tag with `user-scalable=no`

## Color Palette
- Background sky: #87CEEB → #E8F5E9 (gradient)
- Meadow green: #4CAF50
- Hatch gold: #FFD700
- Crystal purple: #9C27B0
- Warm brown (wood/earth): #795548
- Text dark: #2E2E2E
- Button primary: #FF9800
- Button secondary: #42A5F5
- Success green: #66BB6A
- Star yellow: #FFC107

## Typography
- Headings: 'Baloo 2' or system rounded sans-serif
- Body: system sans-serif, 24px minimum
- All text: high contrast, no thin fonts

## File
- Single file: `index.html`
- Host at port 3458
- Self-contained — all CSS/JS inline, SVG art inline
- No external dependencies (works offline)

## Definition of Done
- [ ] Loads on iPad Safari
- [ ] All 5 scenes playable start to finish
- [ ] 2 learning challenges with 3 difficulty tiers each
- [ ] Story branching works (meadow optional path, 3 finale variants)
- [ ] Adaptive difficulty adjusts based on performance
- [ ] Touch interactions feel good (no tiny targets, no double-tap zoom issues)
- [ ] End screen shows stats and cliffhanger
- [ ] Looks like a real game, not a prototype sketch
