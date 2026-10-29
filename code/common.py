"""Shared paths and helpers for the lithosphere-thickness study."""
import os, json, gzip, base64
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
# raw downloads (read in place, never copied into the repo)
RAW = os.environ.get("LITHO_RAW", "/home/claude/hist/_data18/lithosphere-thickness")
# temporary work folder (deleted at the end)
WORK = os.environ.get("LITHO_WORK", "/dev/shm/litho")
NE_COUNTRIES = "/home/claude/hist/food-map/data/world.json"            # Natural Earth admin 0 (simplified), read only
GEONAMES = "/home/claude/hist/sun-and-rain/data/cities_page.json"      # GeoNames cities15000 subset, read only
os.makedirs(WORK, exist_ok=True)

# display and analysis grid: 0.25 degree, cell centres
RES = 0.25
NX, NY = int(360 / RES), int(180 / RES)
LONS = -180 + RES * (np.arange(NX) + .5)
LATS = 90 - RES * (np.arange(NY) + .5)
SITE_URL = "https://maps.tristanhotham.com/lithosphere-thickness/"
REPO_URL = "https://github.com/Tristan-Hotham/lithosphere-thickness"
DOI = "10.5281/zenodo.23782261"
BLOG_URL = "https://blog.tristanhotham.com/2026/10/29/lithosphere-thickness/"
AI_STATEMENT = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
                "prepare the analysis code. I reviewed and checked all text and results.")


def jload(p):
    op = gzip.open if p.endswith(".gz") else open
    with op(p, "rt", encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, p, compact=False):
    with open(p, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1)


def area_w():
    """Cell area weights (proportional to cos latitude) on the 0.25 degree grid, shape (NY, NX)."""
    return np.repeat(np.cos(np.radians(LATS))[:, None], NX, axis=1)


def sample(grid, lat, lon, res=RES):
    """Bilinear sample of a global cell-centred grid (row 0 at the north) at lat, lon; wraps in longitude."""
    ny, nx = grid.shape
    fx = (np.asarray(lon) + 180) / res - .5
    fy = (90 - np.asarray(lat)) / res - .5
    x0 = np.floor(fx).astype(int); y0 = np.clip(np.floor(fy).astype(int), 0, ny - 2)
    tx = fx - x0; ty = np.clip(fy - y0, 0, 1)
    x0 %= nx; x1 = (x0 + 1) % nx
    g = grid
    v = (g[y0, x0] * (1 - tx) * (1 - ty) + g[y0, x1] * tx * (1 - ty) + g[y0 + 1, x0] * (1 - tx) * ty + g[y0 + 1, x1] * tx * ty)
    return v


def wmedian(v, w):
    o = np.argsort(v); c = np.cumsum(w[o]); return float(v[o][np.searchsorted(c, c[-1] / 2)])


def wquant(v, w, q):
    o = np.argsort(v); c = np.cumsum(w[o]) / w.sum(); return float(v[o][min(len(v) - 1, np.searchsorted(c, q))])


def hav_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(np.asarray(lon2) - lon1); dp = p2 - p1
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def load_cmap(name):
    return np.loadtxt(os.path.join(HERE, "cmaps", name + ".txt"))
