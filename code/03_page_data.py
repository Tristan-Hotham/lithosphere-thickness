"""Step 3. Page assets in data/:
  grid_a.png  1440 x 720, 0.25 degree cells, row 0 at 90N, column 0 at 180W.
              R = LithoRef18 thickness, G = WINTERC-G thickness: code = round(km / 1.25) + 1.
              B = sea-floor age: code = round(Myr / 1.4) + 1, 0 = no oceanic crust.
  grid_b.png  R = plate index + 1, G = country index + 1 (0 = none), B = LithoRef18 crust thickness km + 1.
  points.json cities (GeoNames, 100,000 or more), volcanoes, diamond sites, plate and country names, area CDFs.
  boundaries.json  PB2002 plate boundaries (Bird 2003), coordinates rounded to 0.01 degree.
  world.json  Natural Earth country outlines (simplified), for the page's own coast and border lines.
  crameri_lithosphere_thickness.jpg  Fabio Crameri's s-Ink map (CC BY-SA 4.0), reduced for the page.
"""
import io
import numpy as np
from PIL import Image
from common import *

g = np.load(f"{WORK}/grids.npz"); r = np.load(f"{WORK}/rasters.npz")
L18, WG, AGE, CR = g["litho18"], g["winterc"], g["age"], g["crust18"]
A = np.zeros((NY, NX, 3), np.uint8)
A[..., 0] = np.clip(np.round(L18 / 1.25) + 1, 1, 255)
A[..., 1] = np.clip(np.round(WG / 1.25) + 1, 1, 255)
A[..., 2] = np.where(np.isnan(AGE), 0, np.clip(np.round(np.nan_to_num(AGE) / 1.4) + 1, 1, 255))
Image.fromarray(A).save(f"{DATA}/grid_a.png", optimize=True)
B = np.zeros((NY, NX, 3), np.uint8)
B[..., 0] = (r["plate"] + 1).clip(0, 255); B[..., 1] = (r["ctry"] + 1).clip(0, 255); B[..., 2] = np.clip(np.round(CR) + 1, 1, 255)
assert r["ctry"].max() < 255 and r["plate"].max() < 255
Image.fromarray(B).save(f"{DATA}/grid_b.png", optimize=True)
err = max(float(np.abs((A[..., 0] - 1) * 1.25 - L18).max()), float(np.abs((A[..., 1] - 1) * 1.25 - WG).max()))
print("max thickness encoding error km", err)

# area CDFs: share of the Earth's surface thinner than x km, x = 0, 2, ..., 300
Wt = area_w(); xs = np.arange(0, 302, 2)
def cdf(v):
    o = np.argsort(v.ravel()); vv = v.ravel()[o]; cw = np.cumsum(Wt.ravel()[o]) / Wt.sum()
    return [round(float(cw[np.searchsorted(vv, x) - 1]) if np.searchsorted(vv, x) > 0 else 0.0, 4) for x in xs]
P = jload(f"{WORK}/points.json")
P["cdf"] = {"x": xs.tolist(), "l": cdf(L18), "w": cdf(WG), "a": cdf((L18 + WG) / 2)}
P["enc"] = {"thick": 1.25, "age": 1.4, "nx": NX, "ny": NY, "res": RES}
jsave(P, f"{DATA}/points.json", compact=True)

# plate boundaries
Bd = jload(f"{RAW}/pb2002_boundaries.json")
feats = []
for f in Bd["features"]:
    gm = f["geometry"]; lines = gm["coordinates"] if gm["type"] == "MultiLineString" else [gm["coordinates"]]
    for ln in lines:
        c = [[round(x, 2), round(y, 2)] for x, y in ln]
        feats.append({"t": "s" if f["properties"].get("Type") == "subduction" else "o", "n": f["properties"]["Name"], "c": c})
jsave({"source": "PB2002, Bird (2003), via github.com/fraxen/tectonicplates (ODC-BY 1.0)", "lines": feats}, f"{DATA}/boundaries.json", compact=True)

# world outlines (rings only, 0.01 degree)
W = jload(NE_COUNTRIES)
rings = []
for f in W["features"]:
    gm = f["geometry"]; polys = gm["coordinates"] if gm["type"] == "MultiPolygon" else [gm["coordinates"]]
    for p in polys:
        rings.append([[round(x, 2), round(y, 2)] for x, y in p[0]])
jsave({"source": "Natural Earth admin 0 countries (public domain), simplified", "rings": rings}, f"{DATA}/world.json", compact=True)

# Crameri's map, reduced (CC BY-SA 4.0; credit on the page)
S = jload(f"{RAW}/litho_sink_20261029.json.gz")
im = Image.open(io.BytesIO(base64.b64decode(S["files_b64"]["LithosphereThickness_mollweid_lon0_acton_Crameri.png"]))).convert("RGBA")
bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
bg = bg.convert("RGB"); bg = bg.resize((1400, round(1400 * im.size[1] / im.size[0])), Image.LANCZOS)
bg.save(f"{DATA}/crameri_lithosphere_thickness.jpg", quality=84, optimize=True)
for fn in ("grid_a.png", "grid_b.png", "points.json", "boundaries.json", "world.json", "crameri_lithosphere_thickness.jpg"):
    print(fn, os.path.getsize(f"{DATA}/{fn}"))
