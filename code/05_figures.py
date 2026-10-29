"""Step 5. Static figures for the blog (release/blog/b_*.png, 1520 px wide), the paper (release/paper/f_*.png and copies
of the blog figures) and the social card (header.png, 1200 x 630). Numbers from data/results.json and the grids of step 1."""
import csv, shutil
from figstyle import *

R = jload(f"{DATA}/results.json")
g = np.load(f"{WORK}/grids.npz")
L18, WG, AGE = g["litho18"].astype(float), g["winterc"].astype(float), g["age"].astype(float)
AVG = (L18 + WG) / 2
BLOG = os.path.join(ROOT, "release", "blog"); PAP = os.path.join(ROOT, "release", "paper")
os.makedirs(BLOG, exist_ok=True); os.makedirs(PAP, exist_ok=True)
RINGS = world_rings(); PL = plate_lines()
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8")))
VOL = rd(f"{DATA}/volcanoes.csv"); DIA = rd(f"{DATA}/diamond_sites.csv")


def worldmap(ax, grid, cmap, vmin, vmax, width=1520, plates=True, coast=True):
    img, ext = ee_raster(grid, width=width)
    ax.imshow(img, extent=ext, cmap=cmap, vmin=vmin, vmax=vmax, interpolation="bilinear", origin="upper")
    if coast:
        ee_lines(ax, RINGS, color=FG, lw=.35, alpha=.55)
    if plates:
        ee_lines(ax, PL, color=PLATE, lw=.9, alpha=.9)
    ee_outline(ax, color=MUT, lw=.8)
    ax.set_xlim(-XMAX * 1.01, XMAX * 1.01); ax.set_ylim(-YMAX * 1.01, YMAX * 1.01); ax.set_aspect("equal"); ax.axis("off")


def cbar(fig, rect, cmap, vmin, vmax, ticks, label, fs=12):
    cax = fig.add_axes(rect)
    cax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=cmap, extent=(vmin, vmax, 0, 1))
    cax.set_yticks([]); cax.set_xticks(ticks); cax.tick_params(labelsize=fs, length=3)
    for s in cax.spines.values():
        s.set_visible(False)
    cax.set_xlabel(label, fontsize=fs, color=MUT)


def pt(lat, lon):
    x, y = EE.transform(lon, lat); return x, y


# 1. the striking map: average thickness, Equal Earth
fig = plt.figure(figsize=(7.6, 4.55))
ax = fig.add_axes([0, .16, 1, .84]); worldmap(ax, AVG, ACTON, 0, 300)
for s in R["cratons"][:13]:
    if s["name"] in ("Superior craton", "Siberian craton", "West African craton", "Kaapvaal craton", "Yilgarn craton", "Amazonian craton", "Baltic Shield"):
        x, y = pt(s["lat"], s["lon"]); ax.text(x, y, s["name"].replace(" craton", ""), fontsize=8.5, color="white", ha="center", va="center", family=MONO, weight="medium")
cbar(fig, [.2, .1, .6, .035], ACTON, 0, 300, [0, 50, 100, 150, 200, 250, 300], "km down to the base of the lithosphere (average of LithoRef18 and WINTERC-G)", fs=9.5)
save(fig, f"{BLOG}/b_map.png")

# 2. disagreement map
fig = plt.figure(figsize=(7.6, 4.55))
ax = fig.add_axes([0, .16, 1, .84]); worldmap(ax, WG - L18, VIK, -100, 100, plates=False)
cbar(fig, [.2, .1, .6, .035], VIK, -100, 100, [-100, -50, 0, 50, 100], "WINTERC-G minus LithoRef18, km (red: WINTERC-G deeper)", fs=9.5)
save(fig, f"{BLOG}/b_disagree.png")

# 3. ocean thickness against age
A = R["ocean_age"]; mid = [(r["age_from"] + r["age_to"]) / 2 for r in A]
fig, ax = plt.subplots(figsize=(7.6, 4.6)); fig.subplots_adjust(left=.11, right=.97, top=.95, bottom=.15)
for k, c, nm in (("lithoref18", HOT, "LithoRef18"), ("winterc", COOL, "WINTERC-G")):
    ax.fill_between(mid, [r[k + "_p25"] for r in A], [r[k + "_p75"] for r in A], color=c, alpha=.16, lw=0)
    ax.plot(mid, [r[k + "_median"] for r in A], color=c, lw=2.6, marker="o", ms=5, label=nm)
t = np.linspace(0, 200, 400); hs = R["ocean_fit"]["halfspace_c"] * np.sqrt(t); m = hs <= 165
ax.plot(t[m], hs[m], color=MUT, lw=1.6, ls=(0, (5, 4)), label="half-space cooling")
ax.set_xlim(0, 200); ax.set_ylim(0, 165); ax.set_xlabel("age of the sea floor, million years", fontsize=12); ax.set_ylabel("km to the base", fontsize=12)
ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(frameon=False, fontsize=11, loc="lower right")
save(fig, f"{BLOG}/b_ocean.png")

# 4. roots: continents, volcanoes, diamond mines
bins = np.arange(0, 320, 20)
Wt = area_w(); cont = np.isnan(AGE)
hc, _ = np.histogram(AVG[cont], bins=bins, weights=Wt[cont]); hc = hc / hc.sum()
hv, _ = np.histogram([float(r["average_km"]) for r in VOL], bins=bins); hv = hv / hv.sum()
hd, _ = np.histogram([float(r["average_km"]) for r in DIA], bins=bins); hd = hd / hd.sum()
fig, axs = plt.subplots(3, 1, figsize=(7.6, 5.6), sharex=True); fig.subplots_adjust(left=.05, right=.97, top=.93, bottom=.11, hspace=.5)
for ax, h, c, nm in zip(axs, (hc, hv, hd), (DEEP, VOLC, DIAM), ("Continental ground (by area)", f"Volcanoes ({R['volcanoes']['n']:,})", f"Diamond mines ({R['diamonds']['n']})")):
    ax.bar(bins[:-1] + 10, h, width=18, color=c, alpha=.88)
    ax.set_yticks([]); [ax.spines[s].set_visible(False) for s in ("top", "right", "left")]
    ax.text(0, 1.0, nm, transform=ax.transAxes, fontsize=12, va="bottom", weight="medium")
axs[-1].set_xlim(0, 300); axs[-1].set_xlabel("km to the base of the lithosphere (average of the two models)", fontsize=11.5)
save(fig, f"{BLOG}/b_roots.png")

# 5. UK: map and towns
P = sorted(R["uk_places"], key=lambda p: p["a"])
fig = plt.figure(figsize=(7.6, 5.2))
axm = fig.add_axes([0, .02, .42, .96])
ext = (-11, 3, 49.5, 61.2)
sub = AVG[int((90 - ext[3]) / RES):int((90 - ext[2]) / RES), int((ext[0] + 180) / RES):int((ext[1] + 180) / RES)]
axm.imshow(sub, extent=ext, cmap=ACTON, vmin=0, vmax=300, interpolation="bilinear", aspect=1 / np.cos(np.radians(55)))
for ring in RINGS:
    a = np.array(ring)
    if a[:, 0].max() > ext[0] and a[:, 0].min() < ext[1] and a[:, 1].max() > ext[2] and a[:, 1].min() < ext[3]:
        axm.plot(a[:, 0], a[:, 1], color=FG, lw=.5, alpha=.8)
for p in R["uk_places"]:
    if p["name"] in ("London", "Glasgow", "Belfast", "Preston", "Cardiff", "Lerwick", "Penzance"):
        axm.plot(p["lon"], p["lat"], "o", ms=3.5, color=FG); axm.text(p["lon"] + .25, p["lat"], p["name"], fontsize=8.5, va="center", color=FG)
axm.set_xlim(ext[0], ext[1]); axm.set_ylim(ext[2], ext[3]); axm.axis("off")
ax = fig.add_axes([.58, .11, .4, .86])
y = np.arange(len(P))
c = R["models"]["average"]["continent"]
ax.axvspan(c["p25"], c["p75"], color=DEEP, alpha=.08, lw=0)
for i, p in enumerate(P):
    ax.plot([p["l"], p["w"]], [i, i], color=MUT, lw=1.3)
ax.scatter([p["l"] for p in P], y, color=HOT, s=34, zorder=3, label="LithoRef18"); ax.scatter([p["w"] for p in P], y, color=COOL, s=34, zorder=3, label="WINTERC-G")
ax.set_yticks(y); ax.set_yticklabels([p["name"] for p in P], fontsize=10); ax.tick_params(axis="y", length=0)
ax.set_xlim(50, 200); ax.set_xticks([50, 100, 150, 200]); ax.tick_params(axis="x", labelsize=10)
ax.set_xlabel("km to the base", fontsize=10.5); [ax.spines[s].set_visible(False) for s in ("top", "right", "left")]
ax.legend(frameon=False, fontsize=9.5, loc="lower right", handletextpad=.2)
save(fig, f"{BLOG}/b_uk.png")

# paper only: the two models and their difference, and the cell-by-cell agreement
fig = plt.figure(figsize=(7.2, 9.6))
for k, (grid, cm, lo, hi, nm) in enumerate(((L18, ACTON, 0, 300, "(a) LithoRef18"), (WG, ACTON, 0, 300, "(b) WINTERC-G"), (WG - L18, VIK, -100, 100, "(c) WINTERC-G minus LithoRef18"))):
    ax = fig.add_axes([.04, .705 - k * .3, .92, .26]); worldmap(ax, grid, cm, lo, hi, width=1300, plates=False)
    ax.text(-XMAX * 1.0, YMAX * 1.03, nm, fontsize=11, va="bottom", ha="left")
cbar(fig, [.08, .07, .38, .012], ACTON, 0, 300, [0, 100, 200, 300], "(a, b) km", fs=9)
cbar(fig, [.56, .07, .38, .012], VIK, -100, 100, [-100, 0, 100], "(c) km", fs=9)
save(fig, f"{PAP}/f_models.png")
fig, ax = plt.subplots(figsize=(5.2, 4.8)); fig.subplots_adjust(left=.14, right=.97, top=.97, bottom=.12)
H, xe, ye = np.histogram2d(L18.ravel(), WG.ravel(), bins=[np.arange(0, 310, 10)] * 2, weights=Wt.ravel())
H = H / H.sum()
ax.imshow(np.ma.masked_equal(H.T, 0) ** .45, origin="lower", extent=(0, 300, 0, 300), cmap=ACTON)
ax.plot([0, 300], [0, 300], color=FG, ls=(0, (4, 4)), lw=1, alpha=.6)
ax.set_xlabel("LithoRef18, km", fontsize=11); ax.set_ylabel("WINTERC-G, km", fontsize=11)
save(fig, f"{PAP}/f_agree.png")
for f in ("b_map", "b_ocean", "b_roots", "b_uk", "b_disagree"):
    shutil.copy(f"{BLOG}/{f}.png", f"{PAP}/{f.replace('b_', 'f_')}.png")

# social card 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.patch.set_facecolor(BG)
ax = fig.add_axes([.36, .03, .66, .94]); worldmap(ax, AVG, ACTON, 0, 300, width=1300)
fig.text(.04, .86, "How thick is\nthe ground\nbeneath you?", fontproperties=DISP, fontsize=46, va="top", color=FG, linespacing=.95)
fig.text(.04, .36, f"The Earth's rigid shell, from {R['ridge']['lithoref18_median_young']:.0f} km\nat mid-ocean ridges to over 200 km\nunder the oldest continents.", fontproperties=SERP, fontsize=17, va="top", color=FG, linespacing=1.3)
fig.text(.04, .1, "maps.tristanhotham.com/lithosphere-thickness", family=MONO, fontsize=12, color=HOT)
fig.text(.04, .05, "Two open models: LithoRef18 and WINTERC-G", family=MONO, fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done")
