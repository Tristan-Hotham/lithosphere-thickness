"""r/dataisbeautiful collage for lithosphere-thickness: 2400 x 3000 px. Everything is computed from files in the repo
(data/results.json, data/grid_a.png, data/points.json, data/world.json, data/boundaries.json)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from PIL import Image

R = jload(f"{DATA}/results.json"); P = jload(f"{DATA}/points.json")
A = np.asarray(Image.open(f"{DATA}/grid_a.png")).astype(float)
L = (A[..., 0] - 1) * 1.25; W = (A[..., 1] - 1) * 1.25; AGEC = A[..., 2]
AVG = (L + W) / 2
BGC = "#F6F1E7"   # pale chalk
plt.rcParams.update({"axes.facecolor": BGC, "figure.facecolor": BGC, "savefig.facecolor": BGC})
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BGC)

fig.text(.045, .972, "How thick is the ground beneath you?", fontproperties=DISP, fontsize=45, color=FG, va="top")
fig.text(.045, .924, "The Earth's rigid outer shell, the lithosphere, is the plate you stand on. Its base lies anywhere from a few\n"
         "tens of kilometres down at the mid-ocean ridges to more than 200 km under the oldest continents.",
         fontproperties=SERP, fontsize=15.5, color=FG, va="top", linespacing=1.4)

# hero map
ax = fig.add_axes([.05, .525, .9, .345])
img, ext = ee_raster(AVG, width=2300)
ax.imshow(img, extent=ext, cmap=ACTON, vmin=0, vmax=300, interpolation="bilinear")
ee_lines(ax, world_rings(), color=FG, lw=.3, alpha=.5)
ee_lines(ax, plate_lines(), color=PLATE, lw=1.1, alpha=.95)
ee_outline(ax, color=MUT, lw=1)
x0, y0 = EE.transform(-75, -25); x1, _ = EE.transform(45, -25)
xs = np.linspace(-75, 45, 200); px, py = EE.transform(xs, np.full_like(xs, -25.0))
ax.plot(px, py, color=FG, lw=1.6, ls=(0, (4, 3)))
ax.text(px[0] - 2e5, py[0], "slice\nbelow", fontsize=10, ha="right", va="center", color=FG)
for nm, la, lo in (("Baltic Shield", 63, 28), ("Siberia", 65, 110), ("Canadian Shield", 56, -95), ("West Africa", 19, -4), ("Kaapvaal", -27, 26), ("Western Australia", -27, 121), ("Amazonia", -6, -55)):
    x, y = EE.transform(lo, la); ax.text(x, y, nm, fontsize=10.5, color="white", ha="center", va="center", weight="medium")
ax.set_xlim(-XMAX * 1.01, XMAX * 1.01); ax.set_ylim(-YMAX * 1.01, YMAX * 1.01); ax.set_aspect("equal"); ax.axis("off")
cax = fig.add_axes([.3, .515, .4, .008])
cax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=ACTON, extent=(0, 300, 0, 1))
cax.set_yticks([]); cax.set_xticks([0, 100, 200, 300]); cax.tick_params(labelsize=11, length=3)
[s.set_visible(False) for s in cax.spines.values()]
fig.text(.5, .487, "km down to the base of the lithosphere  ·  average of two open models (LithoRef18, WINTERC-G)  ·  orange: plate boundaries",
         fontsize=10.5, color=MUT, ha="center")

# cross-section at 25 S
row = int((90 + 25) / RES)
cols = ((np.arange(-75, 45, .25) + 180) / RES).astype(int)
lon = np.arange(-75, 45, .25)
pl, pw, pa, oc = L[row, cols], W[row, cols], AVG[row, cols], AGEC[row, cols] > 0
axs = fig.add_axes([.07, .345, .88, .11])
axs.fill_between(lon, 0, pa, color=ACTON(.62), alpha=.9, lw=0)
axs.fill_between(lon, pa, 300, color=ACTON(.06), lw=0)
axs.plot(lon, pl, color=HOT, lw=1.6); axs.plot(lon, pw, color=COOL, lw=1.6)
axs.fill_between(lon, -14, 0, where=oc, color="#9CC3DA", lw=0); axs.fill_between(lon, -14, 0, where=~oc, color=SAND, lw=0)
axs.set_ylim(300, -14); axs.set_xlim(-75, 45)
axs.set_yticks([0, 100, 200, 300]); axs.set_ylabel("km down", fontsize=11)
axs.set_xticks([-60, -30, 0, 30]); axs.set_xticklabels(["60°W", "30°W", "0°", "30°E"], fontsize=10.5)
for s in ("top", "right"):
    axs.spines[s].set_visible(False)
ridge = lon[(lon > -25) & (lon < -5)][np.argmin(pl[(lon > -25) & (lon < -5)])]
for nm, x in (("Andes", -68), ("Brazil", -50), ("Mid-Atlantic Ridge", ridge), ("Kaapvaal", 26), ("Indian Ocean", 41)):
    axs.text(x, -20, nm, fontsize=10.5, ha="center", va="bottom", color=FG)
axs.text(-74, 290, "A slice through the Earth at 25°S", fontproperties=DISP6, fontsize=14, color=FG, va="bottom")
axs.text(44, 290, "lines: LithoRef18 (pink), WINTERC-G (blue)", fontsize=10, color=FG, va="bottom", ha="right")

# big numbers
NUM = [(f"{R['models']['average']['all']['mean']:.0f} km", "average thickness of the\nEarth's lithosphere. The two\nmodels agree to within 1 km.", FG),
       (f"{R['ridge']['lithoref18_median_young']:.0f} km", "at the mid-ocean ridges,\nwhere new plate is made\n(LithoRef18, youngest floor)", COOL),
       (f"{R['diamonds']['median_a']:.0f} km", f"typical root under {R['diamonds']['n']}\ndiamond mines: deeper than\n{R['diamonds']['cont_share_thinner_than_median'] * 100:.0f}% of continental ground", HOT),
       (f"{round(R['lancashire']['nearest_deep']['km'], -1):,.0f} km", f"from Lancashire to the nearest\nground deeper than 200 km\nin both models ({R['lancashire']['nearest_deep']['country']})", DEEP)]
for i, (big, small, col) in enumerate(NUM):
    x = .045 + i * .238
    fig.text(x, .308, big, fontproperties=DISP, fontsize=38, color=col, va="top")
    fig.text(x, .263, small, fontsize=11, color=FG, va="top", linespacing=1.4)

# small multiples: ocean age, and where volcanoes and diamonds sit
a1 = fig.add_axes([.07, .121, .38, .046])
OA = R["ocean_age"]; mid = [(r["age_from"] + r["age_to"]) / 2 for r in OA]
a1.plot(mid, [r["lithoref18_median"] for r in OA], color=HOT, lw=2.4, marker="o", ms=4)
a1.plot(mid, [r["winterc_median"] for r in OA], color=COOL, lw=2.4, marker="o", ms=4)
a1.set_xlim(0, 200); a1.set_ylim(0, 140); a1.set_yticks([0, 50, 100]); a1.tick_params(labelsize=10)
a1.set_xlabel("age of the sea floor, million years", fontsize=10.5); a1.set_ylabel("km", fontsize=10.5)
[a1.spines[s].set_visible(False) for s in ("top", "right")]
fig.text(.07, .207, "OCEAN FLOOR THICKENS AS IT AGES\nLithoRef18 (pink), WINTERC-G (blue)", fontsize=11.5, color=MUT, weight="medium", va="top", linespacing=1.4)
a2 = fig.add_axes([.56, .121, .4, .046])
bins = np.arange(0, 320, 20)
hv, _ = np.histogram([v[3] for v in P["volcanoes"]], bins=bins); hd, _ = np.histogram([v[3] for v in P["diamonds"]], bins=bins)
a2.bar(bins[:-1] + 10, hv / hv.sum(), width=18, color=VOLC, alpha=.85, label=f"volcanoes ({len(P['volcanoes']):,})")
a2.bar(bins[:-1] + 10, hd / hd.sum(), width=18, color=DIAM, alpha=.75, label=f"diamond mines ({len(P['diamonds'])})")
a2.set_xlim(0, 300); a2.set_yticks([]); a2.tick_params(labelsize=10); a2.set_xlabel("km to the base of the lithosphere", fontsize=10.5)
[a2.spines[s].set_visible(False) for s in ("top", "right", "left")]
pass
fig.text(.56, .207, "VOLCANOES (RED) ON THIN GROUND,\nDIAMOND MINES (BLUE) ON THICK", fontsize=11.5, color=MUT, weight="medium", va="top", linespacing=1.4)

fig.text(.045, .012, "Data: LithoRef18 (Afonso et al. 2019, via EarthByte, CC BY 4.0); WINTERC-G (Fullea et al. 2021, Zenodo, CC BY 4.0);\n"
         "sea-floor age (Seton et al. 2020, CC BY 4.0); plates PB2002 (Bird 2003, ODC-BY); volcanoes and mines: Wikidata (CC0).\n"
         "Colour map: acton (Crameri). Inspired by Fabio Crameri's s-Ink map of Conrad and Lithgow-Bertelloni (2006), CC BY-SA 4.0.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/lithosphere-thickness",
         fontsize=9.3, color=MUT, va="bottom", linespacing=1.5)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lithosphere_thickness.png"), dpi=200, facecolor=BGC)
print("collage done")
