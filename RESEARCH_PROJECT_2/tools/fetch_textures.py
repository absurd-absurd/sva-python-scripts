"""Download Chapter 2's CC0 photo textures from ambientCG, the same way Chapter 1 does
(RESEARCH_PROJECT_1/tools/fetch_textures.py: its fetch(), into RESEARCH_PROJECT_2/textures).

    python fetch_textures.py
"""
import json
import os

RP1_TOOL = r"C:/Users/fayth/sva-python-scripts/RESEARCH_PROJECT_1/tools/fetch_textures.py"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SURFACES = {
    "sand": "sand",               # the gully floor
    "silt": "mud",                # where the floor rises into the banks
    "clay_bank": "clay",          # the steep banks
}

src = open(RP1_TOOL, encoding="utf-8").read()
ns = {"__name__": "rp1_fetch", "__file__": RP1_TOOL}
exec(src, ns)
ns["OUT"] = os.path.join(ROOT, "textures")
fetch = ns["fetch"]
os.makedirs(ns["OUT"], exist_ok=True)
path = os.path.join(ns["OUT"], "credits.json")
credits = json.load(open(path)) if os.path.exists(path) else {}
for surface, words in SURFACES.items():
    if credits.get(surface) and os.path.exists(os.path.join(ns["OUT"], surface + ".jpg")):
        continue
    credits[surface] = fetch(surface, words)
    print(surface, "<-", credits[surface]["asset"] if credits[surface] else "NOTHING FOUND")
json.dump(credits, open(path, "w"), indent=1)
