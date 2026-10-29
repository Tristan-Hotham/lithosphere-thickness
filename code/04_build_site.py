"""Step 4. Fill code/page_template.html from data/results.json to make index.html.
Placeholders: {{path.to.value|format}}; formats: int, f1, f2, pct, pct1, r10 (nearest ten), ord (73rd). Also embeds
results (/*RESULTS*/), colour tables (/*LUTS*/) and the full-screen map snippet (<!--FULLSCREEN-->)."""
import re
import numpy as np
from common import *

R = jload(f"{DATA}/results.json")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def ordinal(n):
    n = int(n); s = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{s}"


def fmt(v, f):
    if f == "int": return f"{round(v):,}"
    if f == "f1": return f"{v:,.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "r10": return f"{int(round(v, -1)):,}"
    if f == "ord": return ordinal(v)
    return str(v)


def fill(t):
    return re.sub(r"\{\{([\w.]+)(?:\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(2) or "") if m.group(2) else str(get(m.group(1))), t)


if __name__ == "__main__":
    t = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    t = fill(t)
    luts = {}
    for n in ("acton", "vik", "batlow", "lajolla"):
        a = load_cmap(n); idx = np.linspace(0, 255, 64).round().astype(int)
        luts[n] = "".join("%02x%02x%02x" % tuple((a[i] * 255).round().astype(int)) for i in idx)
    t = t.replace("/*RESULTS*/", json.dumps(R, ensure_ascii=False, separators=(",", ":")))
    t = t.replace("/*LUTS*/", json.dumps(luts))
    t = t.replace("<!--FULLSCREEN-->", open(os.path.join(HERE, "fullscreen_snippet.html"), encoding="utf-8").read())
    assert "{{" not in t, re.findall(r"\{\{[^}]+\}\}", t)[:5]
    # facts stated in words that must match the data
    assert R["countries"]["thickest"][0]["country"] == "Lithuania" or "Lithuania" not in t
    assert R["lancashire"]["nearest_deep"]["country"] == "Sweden"
    assert R["cratons"][13]["name"].startswith("North China") and R["contrasts"][3]["name"] == "Tibetan Plateau" and R["uk_places"][10]["name"] == "Preston"
    assert R["big_cities"]["thinnest"][0]["name"] == "Tianjin"
    assert 30 < R["ridge"]["oldest"]["lat"] < 37 and 20 < R["ridge"]["oldest"]["lon"] < 36   # eastern Mediterranean
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
    print("index.html", len(t))
