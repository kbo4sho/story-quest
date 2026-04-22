#!/usr/bin/env python3
"""
Story Quest — LLM vignette proxy (W5).

Reads ANTHROPIC_API_KEY from the environment and forwards structured vignette
requests from the browser-served world runtime to the Anthropic API. Keeps the
API key out of the self-contained HTML so the world can be loaded from any
machine without exposing secrets.

Run alongside the static server:

    export ANTHROPIC_API_KEY=sk-ant-...
    python3 llm_proxy.py                 # defaults to :3459

The world's runtime fetches POST http://localhost:3459/vignette with
{"topic": "..."} and receives a structured vignette JSON blob.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    import anthropic
except ImportError:
    sys.stderr.write(
        "[proxy] Missing 'anthropic' package. Install with:\n"
        "    python3 -m pip install --user anthropic\n"
    )
    sys.exit(1)


PORT = int(os.environ.get("STORY_QUEST_PROXY_PORT", "3459"))
MODEL = os.environ.get("STORY_QUEST_MODEL", "claude-sonnet-4-6")

# Mode selector:
#   "auto"    — try the local library (vignettes.json) first; fall through to
#               live Claude on miss. Also auto-fallback to library-only if
#               ANTHROPIC_API_KEY is missing.
#   "library" — only serve from vignettes.json; return 404 on miss (the
#               browser then falls back to the templated single-NPC scene).
#   "live"    — only call Claude; ignore the library.
MODE = os.environ.get("STORY_QUEST_MODE", "auto").lower()

# Library file lives next to this script. Re-read on every request so we can
# hand-edit / hand-author vignettes during a session without restarting the
# proxy. Each entry: { "match": [keywords...], "vignette": {...} }.
LIBRARY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vignettes.json")


def load_library() -> list:
    """Read vignettes.json fresh each call so edits show up without restart."""
    try:
        with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("vignettes"), list):
            return data["vignettes"]
    except FileNotFoundError:
        return []
    except Exception as exc:
        sys.stderr.write(f"[proxy] vignettes.json read error: {exc}\n")
    return []


def lookup_library(topic: str):
    """Return the first vignette whose `match` keywords intersect the topic."""
    t = topic.lower()
    for entry in load_library():
        for kw in entry.get("match", []):
            if kw and kw.lower() in t:
                return entry.get("vignette")
    return None


# ---------------------------------------------------------------------------
# System prompt — the "world author" that turns a topic into a small teaching
# scene. Kept large on purpose so prompt caching amortizes the cost across
# every question the player asks.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the world-author for Story Quest, a gentle low-poly exploration game for kids ages 5-8.

A child in the game (Leo) walks up to a campfire and asks a question. Your job is to design a small "vignette" — a tiny themed place with 2 to 4 characters on it who, together, teach the topic through dialogue.

OUTPUT
You must return JSON matching the provided schema exactly. No prose outside JSON.

TONE & STYLE
- K-2 reading level. Short sentences, concrete words. No jargon unless the character defines it inside a line.
- Warm, curious, never condescending. Characters talk TO Leo, not AT him.
- Show, don't tell: use little images, examples, and comparisons rather than definitions.
- Dialogue is spoken aloud — write how a friendly grown-up would actually talk, not how a textbook reads.
- Never scary, never sad for sadness's sake. Wonder is the target emotion.

CAST (2-4 characters; 3 is the sweet spot)
- Pick real historical figures, mythological figures, or plausible themed characters tied to the topic.
  - "electricity" → Thomas Edison, Nikola Tesla, Benjamin Franklin.
  - "ocean" → a marine biologist, a dolphin, a tide-pool fisher.
  - "volcanoes" → a geologist, a vulcanologist, maybe Pele from Hawaiian myth.
  - "dinosaurs" → a paleontologist, a friendly T-rex, a Triceratops.
  - "space" → a NASA engineer, an astronaut, Galileo with his old telescope.
- Each character has a clear ANGLE on the topic so the dialogues complement each other rather than repeat.
- Each character has:
  - `name`: first name or full name, as a kid would address them.
  - `role_short`: 1-3 words describing what they are ("inventor", "forest guide", "ancient tree").
  - `appearance_hint`: one of exactly these values — "scholar", "ranger", "tinkerer", "elder", "child", "wild".
  - `dialogue`: 4 to 6 lines. First line introduces the character warmly. Middle lines teach through images and examples. Last line invites wonder or a return visit.
- Dialogue lines are plain strings — no stage directions, no "he says", no quotation marks inside.

POSITION (so the runtime can place each character on the 3D chunk)
- `angleDeg` is 0-360 (0 = east, 90 = north, 180 = west, 270 = south), relative to the scene's center.
- `radius` is world units, 0-12. 0 = exact center of the scene.
- Cluster the cast so they're visible together — typical radius 3-8.
- One character may be at the center (radius 0). Space the others at distinct angles (at least 60° apart).

REGION
- `region_name`: short, evocative. 2-4 words ("Edison's Workshop", "The Tide Pool", "Volcano's Edge").
- `family`: one of exactly these values — "earthen", "watery", "wooded", "airy", "default". Pick the one that matches the topic's visual feel (the game uses this to color terrain, foliage, and props):
  - earthen — rocks, mountains, caves, fossils, deserts, volcanoes, buildings, machinery, history.
  - watery — oceans, rivers, rain, ice, fish, aquatic animals.
  - wooded — forests, trees, plants, land animals, insects, fungi.
  - airy — sky, weather, space, stars, flight, clouds, birds.
  - default — use only when none of the above fit.

EXAMPLE 1 — topic "electricity":
{
  "region_name": "Edison's Workshop",
  "family": "earthen",
  "cast": [
    {
      "name": "Thomas Edison",
      "role_short": "inventor",
      "position": {"angleDeg": 0, "radius": 0},
      "appearance_hint": "tinkerer",
      "dialogue": [
        "Oh, hello! I'm Thomas. Come in — watch your step on those wires.",
        "I spend my days making things that run on electricity. See these glass bulbs?",
        "Inside each one is a tiny thread. When electricity flows through it, the thread gets so hot it glows — like a little captured sun.",
        "Electricity is tiny, tiny pieces called electrons, all pushing each other along a wire.",
        "Try flipping that switch. Watch what happens."
      ]
    },
    {
      "name": "Nikola Tesla",
      "role_short": "engineer",
      "position": {"angleDeg": 135, "radius": 6},
      "appearance_hint": "scholar",
      "dialogue": [
        "Hello, friend. Thomas is clever, but he and I argue about HOW to send electricity.",
        "His way pushes it straight through, always the same direction. Mine zigzags — back, forth, back, forth.",
        "My way, called AC, can travel very far without losing its strength.",
        "That's how the power gets from a big waterfall all the way to your bedroom lamp.",
        "Both our ideas matter. Science grows when people share what they learn."
      ]
    },
    {
      "name": "Benjamin Franklin",
      "role_short": "early experimenter",
      "position": {"angleDeg": 240, "radius": 5},
      "appearance_hint": "elder",
      "dialogue": [
        "Ah, a curious one! I'm Ben. I was asking about electricity long before these two.",
        "A long time ago, people thought lightning was a mystery of the gods.",
        "I tied a key to a kite string one stormy afternoon. Very risky — don't YOU try it!",
        "The sparks told me lightning is the same thing as the little zap you feel from a doorknob.",
        "Every big idea starts with someone brave enough to ask: what IS that, really?"
      ]
    }
  ]
}

EXAMPLE 2 — topic "forest":
{
  "region_name": "Whispering Pines",
  "family": "wooded",
  "cast": [
    {
      "name": "Ranger Maya",
      "role_short": "forest guide",
      "position": {"angleDeg": 0, "radius": 0},
      "appearance_hint": "ranger",
      "dialogue": [
        "Welcome to my woods! I'm Maya. Mind the mushrooms — some are food, some are not.",
        "A forest isn't just trees. It's animals, insects, and helpers too small to see.",
        "Look up — see how the branches reach for the sun? Trees are sunlight-eaters.",
        "Look down. Leaves that fall feed the soil, which feeds next year's seeds.",
        "Everything here is giving to something else. Say hi to the squirrel for me."
      ]
    },
    {
      "name": "Hazel",
      "role_short": "squirrel",
      "position": {"angleDeg": 60, "radius": 5},
      "appearance_hint": "wild",
      "dialogue": [
        "Oh! Hello. I was counting my acorns. I'm Hazel.",
        "Every autumn I bury hundreds of acorns all over the forest floor.",
        "I only dig up about half of them. The rest? They grow into new oak trees!",
        "So squirrels aren't just thieves — we're forest planters without meaning to be.",
        "If you see an oak tree someday, thank a squirrel."
      ]
    },
    {
      "name": "Old Oak",
      "role_short": "ancient tree",
      "position": {"angleDeg": 210, "radius": 7},
      "appearance_hint": "elder",
      "dialogue": [
        "Shhh… listen. The wind is telling old stories.",
        "I am Old Oak. I have stood here for two hundred years.",
        "Beneath the ground, my roots touch the roots of every other tree. We share food, and warnings.",
        "When one of us is thirsty, the others send water. Yes — trees help each other.",
        "Stay curious, small traveler. The forest remembers every child who listens."
      ]
    }
  ]
}

Now produce the vignette for the user's brief. Return JSON only — no prose, no code fences."""


# Anthropic API enforces this strict JSON Schema on the response via
# output_config.format. additionalProperties:false is required at every level.
VIGNETTE_SCHEMA = {
    "type": "object",
    "properties": {
        "region_name": {"type": "string"},
        "family": {
            "type": "string",
            "enum": ["earthen", "watery", "wooded", "airy", "default"],
        },
        "cast": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role_short": {"type": "string"},
                    "position": {
                        "type": "object",
                        "properties": {
                            "angleDeg": {"type": "number"},
                            "radius": {"type": "number"},
                        },
                        "required": ["angleDeg", "radius"],
                        "additionalProperties": False,
                    },
                    "appearance_hint": {
                        "type": "string",
                        "enum": ["scholar", "ranger", "tinkerer", "elder", "child", "wild"],
                    },
                    "dialogue": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "name",
                    "role_short",
                    "position",
                    "appearance_hint",
                    "dialogue",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["region_name", "family", "cast"],
    "additionalProperties": False,
}


client = anthropic.Anthropic() if os.environ.get("ANTHROPIC_API_KEY") else None


def generate_vignette(topic: str) -> dict:
    """Call Claude with the cached system prompt and return the vignette JSON."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Brief: {topic}\n\nReturn the vignette JSON now.",
            }
        ],
        output_config={
            "format": {"type": "json_schema", "schema": VIGNETTE_SCHEMA},
        },
    )

    # Log cache telemetry to stderr so we can eyeball hit rates while developing.
    u = resp.usage
    sys.stderr.write(
        "[proxy] usage "
        f"input={u.input_tokens} "
        f"cache_write={getattr(u, 'cache_creation_input_tokens', 0)} "
        f"cache_read={getattr(u, 'cache_read_input_tokens', 0)} "
        f"output={u.output_tokens}\n"
    )

    for block in resp.content:
        if block.type == "text":
            return json.loads(block.text)
    raise RuntimeError("Claude response had no text block")


# ---------------------------------------------------------------------------
# HTTP handler — minimal, synchronous. ThreadingHTTPServer lets parallel
# requests run, which matters if the player spams the campfire.
# ---------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "content-type")

    def _json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"ok": True, "model": MODEL})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/vignette":
            self._json(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("content-length") or 0)
            body = self.rfile.read(length) if length else b"{}"
            data = json.loads(body or b"{}")
            topic = (data.get("topic") or "").strip()
            if not topic:
                self._json(400, {"error": "missing topic"})
                return

            # Library lookup (auto + library modes).
            if MODE in ("auto", "library"):
                hit = lookup_library(topic)
                if hit is not None:
                    sys.stderr.write(f"[proxy] library hit: {topic!r}\n")
                    self._json(200, hit)
                    return
                if MODE == "library":
                    sys.stderr.write(f"[proxy] library miss (library mode): {topic!r}\n")
                    self._json(404, {"error": "no vignette for topic", "topic": topic})
                    return

            # Live Claude path (auto + live modes).
            if client is None:
                sys.stderr.write(f"[proxy] no API key + library miss: {topic!r}\n")
                self._json(404, {"error": "no vignette for topic and no API key", "topic": topic})
                return
            sys.stderr.write(f"[proxy] live Claude call: {topic!r}\n")
            result = generate_vignette(topic)
            self._json(200, result)
        except anthropic.APIError as exc:  # typed Anthropic errors
            self._json(
                502,
                {
                    "error": str(exc),
                    "type": type(exc).__name__,
                    "status": getattr(exc, "status_code", None),
                },
            )
        except Exception as exc:
            self._json(500, {"error": str(exc), "type": type(exc).__name__})

    # Quieter logs — default BaseHTTPRequestHandler spams stderr.
    def log_message(self, fmt, *args):
        sys.stderr.write("[proxy] " + (fmt % args) + "\n")


def main():
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if MODE == "live" and not has_key:
        sys.stderr.write(
            "[proxy] MODE=live but ANTHROPIC_API_KEY is not set. Export it or\n"
            "        switch to STORY_QUEST_MODE=library / auto.\n"
        )
        sys.exit(1)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    key_status = "with key" if has_key else "no key"
    lib = load_library()
    sys.stderr.write(
        f"[proxy] Story Quest vignette proxy on http://localhost:{PORT}\n"
        f"        mode={MODE}  model={MODEL}  {key_status}  library={len(lib)} entries\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\n[proxy] shutting down\n")


if __name__ == "__main__":
    main()
