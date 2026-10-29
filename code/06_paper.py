"""Step 6. Build the paper PDF: fill code/paper_template.tex from data/results.json, write release/paper/Hotham_Lithosphere_Thickness.tex
and compile with xelatex (figures from step 5). Copies the PDF to release/."""
import re, shutil, subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Lithosphere_Thickness"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def ordinal(n):
    n = int(n); return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def fmt(v, f):
    if f == "int": return f"{round(v):,}"
    if f == "f1": return f"{v:,.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "pct": return f"{round(v * 100)}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "r10": return f"{int(round(v, -1)):,}"
    if f == "ord": return ordinal(v)
    return tex(v)


M = R["models"]
rows = ""
for k, nm in (("lithoref18", "LithoRef18"), ("winterc", "WINTERC-G"), ("average", "Mean of both")):
    for z, zn in (("all", "All"), ("continent", "Continental"), ("ocean", "Oceanic")):
        s = M[k][z]
        rows += f"{nm if z == 'all' else ''} & {zn} & {s['mean']:.0f} & {s['median']:.0f} & {s['p10']:.0f} to {s['p90']:.0f} & {s['share_under_100'] * 100:.0f} & {s['share_over_200'] * 100:.1f}\\\\\n"
    rows += "\\addlinespace\n" if k != "average" else ""
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Area-weighted summaries of lithosphere thickness (km) and shares of area (\\%). "
      "Continental: cells without oceanic crust in the age grid of Seton et al. (2020).}\\label{tab:global}"
      "\\begin{tabular}{llrrrrr}\\toprule Model & Area & Mean & Median & 10th to 90th & Under 100 km & Over 200 km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for s in R["cratons"] + R["contrasts"]:
    rows += f"{tex(s['name'])} & {tex(s['where'])} & {abs(s['lat']):.1f}\\textdegree\\,{'N' if s['lat'] >= 0 else 'S'}, {abs(s['lon']):.1f}\\textdegree\\,{'E' if s['lon'] >= 0 else 'W'} & {s['l']:.0f} & {s['w']:.0f} & {s['crust']:.0f}\\\\\n"
    if s is R["cratons"][-1]:
        rows += "\\midrule\n"
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Lithosphere thickness (km) at approximate craton centres and contrasting places. "
      "Points chosen from general geological maps; crust from LithoRef18.}\\label{tab:cratons}"
      "\\begin{tabular}{lllrrr}\\toprule Place & Where & Point & LithoRef18 & WINTERC-G & Crust\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
allc = R["countries"]["all"]
for i, r in enumerate(allc[:8]):
    rows += f"{i + 1} & {tex(r['country'])} & {r['a']} & {r['l']} & {r['w']}\\\\\n"
rows += "\\midrule\n"
uk = next(i for i, r in enumerate(allc) if r["iso"] == "GBR")
rows += f"{uk + 1} & United Kingdom & {allc[uk]['a']} & {allc[uk]['l']} & {allc[uk]['w']}\\\\\n\\midrule\n"
n = len(allc)
for i, r in list(enumerate(allc))[-8:]:
    rows += f"{i + 1} & {tex(r['country'])} & {r['a']} & {r['l']} & {r['w']}\\\\\n"
TN = ("\\begin{table}[tbp]\\centering\\small\\caption{Area-weighted mean lithosphere thickness (km) by country: the eight thickest, the United Kingdom and the eight thinnest of "
      f"{n} countries with at least 20,000 km\\textsuperscript{{2}} in the grid.}}\\label{{tab:countries}}"
      "\\begin{tabular}{rlrrr}\\toprule Rank & Country & Mean of both & LithoRef18 & WINTERC-G\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(HERE, "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{TABLE_GLOBAL}}", TG).replace("{{TABLE_CRATONS}}", TC).replace("{{TABLE_COUNTRIES}}", TN)
t = re.sub(r"\{\{([\w.]+)(?:\|(\w+))?\}\}", lambda m: fmt(get(m.group(1)), m.group(2) or "raw"), t)
assert "{{" not in t and "--" not in t and "\u2013" not in t and "\u2014" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    p = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if p.returncode:
    print(p.stdout[-3000:])
for ext in (".aux", ".log", ".out"):
    try: os.remove(os.path.join(OUT, NAME + ext))
    except FileNotFoundError: pass
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("pdf", os.path.getsize(os.path.join(ROOT, "release", NAME + ".pdf")))
