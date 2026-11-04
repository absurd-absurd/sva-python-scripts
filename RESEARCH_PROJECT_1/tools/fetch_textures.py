"""Download the CC0 photo textures MARROW uses, from ambientCG (public domain).

    python fetch_textures.py

For each surface below it searches ambientCG, takes the first result, downloads its
1K JPG pack and keeps only the color map as textures/<surface>.jpg. Unreal shrinks them
to PS2 size on import. Which texture went where is written to textures/credits.json.
"""
import io
import json
import os
import urllib.parse
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "textures")
API = "https://ambientcg.com/api/v2/full_json?type=Material&limit=1&include=downloadData&sort=Popular&"
UA = {"User-Agent": "marrow-texture-fetch/1.0"}

# surface name -> search words on ambientCG, or "id:<AssetId>" for an exact texture
SURFACES = {
    "asphalt": "road cracked",
    "concrete": "id:Concrete048",
    "plaster": "plaster",
    "bricks": "bricks",
    "wood_siding": "wood siding",
    "planks": "planks",
    "painted_wood": "painted wood",
    "roof": "roofing",
    "bark": "bark",
    "forest_floor": "forest ground",
    "dirt": "ground dirt",
    "rock": "id:Rock064",
    "rust": "rust",
    "painted_metal": "painted metal",
    "carpet": "carpet",
    "fabric": "fabric",
    "grass": "grass",
}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


def fetch(surface, words):
    query = "id=" + words[3:] if words.startswith("id:") else "q=" + urllib.parse.quote(words)
    found = json.loads(get(API + query))["foundAssets"]
    if not found:
        return None
    asset = found[0]
    zips = asset["downloadFolders"]["default"]["downloadFiletypeCategories"]["zip"]["downloads"]
    link = next(d["downloadLink"] for d in zips if d["attribute"] == "1K-JPG")
    with zipfile.ZipFile(io.BytesIO(get(link))) as z:
        color = next(n for n in z.namelist() if n.lower().endswith("_color.jpg"))
        with open(os.path.join(OUT, surface + ".jpg"), "wb") as f:
            f.write(z.read(color))
    return {"asset": asset["assetId"], "url": f"https://ambientcg.com/view?id={asset['assetId']}", "license": "CC0"}


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "credits.json")
    credits = json.load(open(path)) if os.path.exists(path) else {}
    for surface, words in SURFACES.items():
        have = credits.get(surface) and os.path.exists(os.path.join(OUT, surface + ".jpg"))
        pinned_changed = have and words.startswith("id:") and credits[surface]["asset"] != words[3:]
        if have and not pinned_changed:
            continue                                  # already downloaded
        try:
            credits[surface] = fetch(surface, words)
            print(f"{surface:14s} <- {credits[surface]['asset'] if credits[surface] else 'NOTHING FOUND'}")
        except Exception as e:                       # one failed texture shouldn't stop the rest
            print(f"{surface:14s} FAILED: {e}")
    with open(path, "w") as f:
        json.dump(credits, f, indent=1)


if __name__ == "__main__":
    main()
