"""Step 2. All statistics. Reads WORK/grids.npz (step 1) and the point layers; writes data/*.csv and data/results.json.
Every number used on the page, in the paper, the blog and the collage comes from results.json."""
import csv, re
import numpy as np
from matplotlib.path import Path
from common import *

g = np.load(f"{WORK}/grids.npz")
L18, WG, AGE, CR = g["litho18"].astype(float), g["winterc"].astype(float), g["age"].astype(float), g["crust18"].astype(float)
AVG = (L18 + WG) / 2
Wt = area_w()
OCEAN = ~np.isnan(AGE)
CONT = ~OCEAN
LO, LA = np.meshgrid(LONS, LATS)
R = {"meta": {}, "models": {}}
EARTH_KM2 = 510.07e6


def stats(v, m):
    vv, ww = v[m], Wt[m]
    return {"mean": float((vv * ww).sum() / ww.sum()), "median": wmedian(vv, ww),
            "p10": wquant(vv, ww, .1), "p25": wquant(vv, ww, .25), "p75": wquant(vv, ww, .75), "p90": wquant(vv, ww, .9),
            "share_over_200": float(ww[vv > 200].sum() / ww.sum()), "share_over_150": float(ww[vv > 150].sum() / ww.sum()),
            "share_under_100": float(ww[vv < 100].sum() / ww.sum()), "share_under_50": float(ww[vv < 50].sum() / ww.sum())}


R["meta"]["grid_res_deg"] = RES
R["meta"]["ocean_share"] = float(Wt[OCEAN].sum() / Wt.sum())
R["meta"]["lithoref18_points"] = int(g["g18_thick"].size)
R["meta"]["winterc_nodes"] = 12232
for name, v in (("lithoref18", L18), ("winterc", WG), ("average", AVG)):
    R["models"][name] = {"all": stats(v, np.ones_like(OCEAN)), "continent": stats(v, CONT), "ocean": stats(v, OCEAN)}
    R["models"][name]["area_over_200_mkm2"] = float(Wt[v > 200].sum() / Wt.sum() * EARTH_KM2 / 1e6)

# extremes on the native grids (no interpolation)
G2 = g["g18_thick"]; lons2 = np.arange(-179, 180, 2.0); lats2 = np.arange(89, -90, -2.0)
iy, ix = np.unravel_index(np.argmax(G2), G2.shape); jy, jx = np.unravel_index(np.argmin(G2), G2.shape)
R["models"]["lithoref18"]["max"] = {"km": float(G2[iy, ix]), "lat": float(lats2[iy]), "lon": float(lons2[ix])}
R["models"]["lithoref18"]["min"] = {"km": float(G2[jy, jx]), "lat": float(lats2[jy]), "lon": float(lons2[jx])}
Wp = np.loadtxt(f"{DATA}/winterc_g_lab_points.csv", delimiter=",", skiprows=1)
R["models"]["winterc"]["max"] = {"km": float(Wp[:, 3].max()), "n_at_max": int((Wp[:, 3] >= 299.99).sum())}
k = np.argmin(Wp[:, 3]); R["models"]["winterc"]["min"] = {"km": float(Wp[k, 3]), "lat": float(Wp[k, 2]), "lon": float(Wp[k, 1]), "n_at_min": int((Wp[:, 3] <= 45.01).sum())}

# agreement between the two models
d = WG - L18
ww = Wt.ravel()
def wcorr(a, b, w):
    am, bm = (a * w).sum() / w.sum(), (b * w).sum() / w.sum()
    return float(((a - am) * (b - bm) * w).sum() / np.sqrt(((a - am) ** 2 * w).sum() * ((b - bm) ** 2 * w).sum()))
R["agree"] = {"r_all": wcorr(L18.ravel(), WG.ravel(), ww),
              "r_continent": wcorr(L18[CONT], WG[CONT], Wt[CONT]), "r_ocean": wcorr(L18[OCEAN], WG[OCEAN], Wt[OCEAN]),
              "median_absdiff": wmedian(np.abs(d).ravel(), ww), "median_absdiff_continent": wmedian(np.abs(d[CONT]), Wt[CONT]),
              "median_absdiff_ocean": wmedian(np.abs(d[OCEAN]), Wt[OCEAN]),
              "share_diff_over_50": float(Wt[np.abs(d) > 50].sum() / Wt.sum()),
              "mean_diff_w_minus_l": float((d * Wt).sum() / Wt.sum()),
              "both_over_200_mkm2": float(Wt[(L18 > 200) & (WG > 200)].sum() / Wt.sum() * EARTH_KM2 / 1e6),
              "either_over_200_mkm2": float(Wt[(L18 > 200) | (WG > 200)].sum() / Wt.sum() * EARTH_KM2 / 1e6)}

# ocean: thickness against age of the sea floor
edges = [0, 2, 5, 10, 20, 30, 40, 50, 60, 80, 100, 120, 140, 160, 200]
rows = []
for a0, a1 in zip(edges[:-1], edges[1:]):
    m = OCEAN & (AGE >= a0) & (AGE < a1)
    rows.append({"age_from": a0, "age_to": a1, "area_share_of_ocean": float(Wt[m].sum() / Wt[OCEAN].sum()),
                 "lithoref18_median": wmedian(L18[m], Wt[m]), "winterc_median": wmedian(WG[m], Wt[m]),
                 "lithoref18_p25": wquant(L18[m], Wt[m], .25), "lithoref18_p75": wquant(L18[m], Wt[m], .75),
                 "winterc_p25": wquant(WG[m], Wt[m], .25), "winterc_p75": wquant(WG[m], Wt[m], .75)})
R["ocean_age"] = rows
with open(f"{DATA}/ocean_thickness_by_age.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); [w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}) for r in rows]
# fit thickness = c * sqrt(age) on young sea floor (0 to 80 Myr), weighted least squares through the origin
fit = {}
for name, v in (("lithoref18", L18), ("winterc", WG)):
    m = OCEAN & (AGE > 0) & (AGE < 80)
    s = np.sqrt(AGE[m]); c = float((Wt[m] * s * v[m]).sum() / (Wt[m] * s * s).sum())
    m2 = OCEAN & (AGE > 0)
    rr = float(np.corrcoef(np.sqrt(AGE[m2]), v[m2])[0, 1])
    fit[name] = {"c_km_per_sqrt_myr": c, "r_sqrt_age_all_ocean": rr}
# textbook half-space cooling (Turcotte and Schubert): thermal boundary layer thickness 2.32 sqrt(kappa t), kappa = 1e-6 m2/s
fit["halfspace_c"] = 2.32 * np.sqrt(1e-6 * 3.15576e13) / 1000
R["ocean_fit"] = fit
young = OCEAN & (AGE < 2); old = OCEAN & (AGE >= 150)
R["ridge"] = {"young_cells_share_of_ocean": float(Wt[young].sum() / Wt[OCEAN].sum()),
              "lithoref18_median_young": wmedian(L18[young], Wt[young]), "winterc_median_young": wmedian(WG[young], Wt[young]),
              "lithoref18_median_old": wmedian(L18[old], Wt[old]), "winterc_median_old": wmedian(WG[old], Wt[old]),
              "age_max_myr": float(np.nanmax(AGE)), "oldest_lat": float(LA[np.nanargmax(np.where(OCEAN, AGE, -1)) // NX, 0])}
iy, ix = np.unravel_index(np.nanargmax(np.where(OCEAN, AGE, -1)), AGE.shape)
R["ridge"]["oldest"] = {"lat": float(LATS[iy]), "lon": float(LONS[ix]), "age": float(AGE[iy, ix])}


# rasterise polygons to the 0.25 degree grid
def raster(features, keyf):
    out = np.full((NY, NX), -1, np.int16); names = []
    pts = np.column_stack([LO.ravel(), LA.ravel()])
    for i, f in enumerate(features):
        geom = f["geometry"]; polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        names.append(keyf(f))
        for poly in polys:
            ring = np.array(poly[0])
            if len(ring) < 3:
                continue
            x0, y0 = ring.min(0); x1, y1 = ring.max(0)
            c0, c1 = int((x0 + 180) / RES), int(np.ceil((x1 + 180) / RES)); r0, r1 = int((90 - y1) / RES), int(np.ceil((90 - y0) / RES))
            c0, r0 = max(c0, 0), max(r0, 0); c1, r1 = min(c1, NX), min(r1, NY)
            sub = np.column_stack([LO[r0:r1, c0:c1].ravel(), LA[r0:r1, c0:c1].ravel()])
            inside = Path(ring).contains_points(sub).reshape(r1 - r0, c1 - c0)
            for h in poly[1:]:
                hr = np.array(h)
                if len(hr) >= 3:
                    inside &= ~Path(hr).contains_points(sub).reshape(r1 - r0, c1 - c0)
            blk = out[r0:r1, c0:c1]; blk[inside] = i
    return out, names


W = jload(NE_COUNTRIES)
CTRY, cnames = raster(W["features"], lambda f: (f["properties"]["iso"], f["properties"]["name"]))
P = jload(f"{RAW}/pb2002_plates.json")
PLATE, pnames = raster(P["features"], lambda f: (f["properties"]["Code"], f["properties"]["PlateName"]))
# PB2002 polygons cover the globe; fill any gaps from the nearest assigned cell along the row
miss = PLATE < 0
R["meta"]["plate_gap_cells"] = int(miss.sum())
for y in range(NY):
    row = PLATE[y]
    if (row < 0).any() and (row >= 0).any():
        good = np.where(row >= 0)[0]; bad = np.where(row < 0)[0]
        idx = np.searchsorted(good, bad).clip(0, len(good) - 1); row[bad] = row[good[idx]]
np.savez_compressed(f"{WORK}/rasters.npz", ctry=CTRY, plate=PLATE)

ctab = []
for i, (iso, nm) in enumerate(cnames):
    m = CTRY == i
    if not m.any():
        continue
    a = float(Wt[m].sum() / Wt.sum() * EARTH_KM2)
    ctab.append({"iso": iso, "country": nm, "area_km2_grid": round(a), "cells": int(m.sum()),
                 "lithoref18_mean": float((L18[m] * Wt[m]).sum() / Wt[m].sum()), "winterc_mean": float((WG[m] * Wt[m]).sum() / Wt[m].sum()),
                 "average_mean": float((AVG[m] * Wt[m]).sum() / Wt[m].sum()), "average_max": float(AVG[m].max()), "average_min": float(AVG[m].min()),
                 "crust_mean": float((CR[m] * Wt[m]).sum() / Wt[m].sum())})
ctab.sort(key=lambda r: -r["average_mean"])
with open(f"{DATA}/countries.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ctab[0].keys())); w.writeheader()
    [w.writerow({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()}) for r in ctab]
big = [r for r in ctab if r["area_km2_grid"] >= 20000]
R["countries"] = {"n_big": len(big), "thickest": big[:10], "thinnest": big[::-1][:10]}
uk = next(r for r in big if r["iso"] == "GBR")
R["uk"] = {"country": uk, "rank_thickest": [r["iso"] for r in big].index("GBR") + 1}
R["countries"]["all"] = [{"iso": r["iso"], "country": r["country"], "l": round(r["lithoref18_mean"]), "w": round(r["winterc_mean"]), "a": round(r["average_mean"]),
                          "area": r["area_km2_grid"]} for r in big]

ptab = []
for i, (code, nm) in enumerate(pnames):
    m = PLATE == i
    if not m.any():
        continue
    ptab.append({"code": code, "plate": nm, "area_share": float(Wt[m].sum() / Wt.sum()),
                 "lithoref18_mean": float((L18[m] * Wt[m]).sum() / Wt[m].sum()), "winterc_mean": float((WG[m] * Wt[m]).sum() / Wt[m].sum()),
                 "average_mean": float((AVG[m] * Wt[m]).sum() / Wt[m].sum()), "ocean_share": float(Wt[m & OCEAN].sum() / Wt[m].sum())})
ptab.sort(key=lambda r: -r["area_share"])
with open(f"{DATA}/plates.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(ptab[0].keys())); w.writeheader()
    [w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}) for r in ptab]
R["plates"] = {"n": len(ptab), "big": [r for r in ptab if r["area_share"] > .01]}


def at(lat, lon):
    def s(G):
        return float(sample(G, lat, lon))
    iy = int((90 - lat) / RES); ix = int((lon + 180) / RES) % NX
    a = AGE[iy, ix]
    return {"lat": lat, "lon": lon, "l": s(L18), "w": s(WG), "a": s(AVG), "crust": s(CR), "age": None if np.isnan(a) else float(a),
            "plate": pnames[PLATE[iy, ix]][1] if PLATE[iy, ix] >= 0 else None}


# cratons and contrasts: representative points (approximate centres from general geological knowledge; see README)
SITES = [("Superior craton", "Canada", 50.0, -85.0), ("Slave craton", "Canada", 64.5, -111.0), ("Siberian craton", "Russia", 65.0, 110.0),
         ("Baltic Shield", "Finland", 63.0, 28.0), ("West African craton", "Mali and Mauritania", 19.0, -4.0),
         ("Congo craton", "DR Congo", -2.0, 22.0), ("Kaapvaal craton", "South Africa", -27.0, 26.0), ("Zimbabwe craton", "Zimbabwe", -19.5, 30.0),
         ("Tanzania craton", "Tanzania", -4.0, 34.0), ("Yilgarn craton", "Western Australia", -29.0, 119.0),
         ("Amazonian craton", "Brazil", -5.0, -55.0), ("Sao Francisco craton", "Brazil", -13.0, -43.0), ("Dharwar craton", "India", 14.0, 76.0),
         ("North China craton (east)", "China", 38.0, 116.0)]
CONTRAST = [("Iceland", "Iceland", 64.9, -18.5), ("Afar", "Ethiopia", 11.5, 41.5), ("Basin and Range", "Nevada, USA", 39.5, -116.5),
            ("Tibetan Plateau", "China", 32.0, 88.0), ("Hawaii", "USA", 19.6, -155.5)]
R["cratons"] = [dict(name=n, where=c, **at(la, lo)) for n, c, la, lo in SITES]
R["contrasts"] = [dict(name=n, where=c, **at(la, lo)) for n, c, la, lo in CONTRAST]
R["cratons_summary"] = {"n": len(SITES), "median_l": float(np.median([s["l"] for s in R["cratons"]])), "median_w": float(np.median([s["w"] for s in R["cratons"]])),
                        "n_over_150_both": sum(1 for s in R["cratons"] if s["l"] > 150 and s["w"] > 150)}

# cities: GeoNames cities15000 (via the sun-and-rain page list), places of 100,000 or more for the page
GN = jload(GEONAMES)
ccn = GN["countries"]
cities = [dict(name=r[0], cc=r[1], lat=r[2], lon=r[3], pop=r[4]) for r in GN["rows"] if r[4] >= 100000]
la = np.array([c["lat"] for c in cities]); lo = np.array([c["lon"] for c in cities])
cl, cw = sample(L18, la, lo), sample(WG, la, lo)
for c, a, b in zip(cities, cl, cw):
    c["l"], c["w"] = round(float(a), 1), round(float(b), 1); c["a"] = round((c["l"] + c["w"]) / 2, 1)
with open(f"{DATA}/cities.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["name", "country_code", "country", "lat", "lon", "population", "lithoref18_km", "winterc_km", "average_km"])
    for c in cities:
        w.writerow([c["name"], c["cc"], ccn.get(c["cc"], ""), c["lat"], c["lon"], c["pop"], c["l"], c["w"], c["a"]])
mil = [c for c in cities if c["pop"] >= 1e6]
mil.sort(key=lambda c: -c["a"])
pick = lambda c: {k: c[k] for k in ("name", "cc", "lat", "lon", "pop", "l", "w", "a")} | {"country": ccn.get(c["cc"], c["cc"])}
R["big_cities"] = {"n": len(mil), "thickest": [pick(c) for c in mil[:10]], "thinnest": [pick(c) for c in mil[::-1][:10]],
                   "median_a": float(np.median([c["a"] for c in mil])),
                   "share_people_on_over_150": float(sum(c["pop"] for c in mil if c["a"] > 150) / sum(c["pop"] for c in mil))}
R["meta"]["cities_page"] = len(cities)

# UK and Lancashire places (coordinates: GeoNames where listed, otherwise rounded town centres)
UKP = [("London", 51.509, -0.126), ("Birmingham", 52.481, -1.900), ("Manchester", 53.481, -2.237), ("Leeds", 53.797, -1.548),
       ("Glasgow", 55.865, -4.258), ("Edinburgh", 55.953, -3.193), ("Cardiff", 51.480, -3.180), ("Belfast", 54.597, -5.930),
       ("Lerwick", 60.155, -1.145), ("Penzance", 50.119, -5.537), ("Preston", 53.763, -2.703), ("Lancaster", 54.047, -2.801),
       ("Blackburn", 53.750, -2.483), ("Clitheroe", 53.871, -2.393), ("Blackpool", 53.817, -3.050)]
R["uk_places"] = [dict(name=n, **at(la_, lo_)) for n, la_, lo_ in UKP]
R["lancashire"] = {"l": float(np.mean([p["l"] for p in R["uk_places"] if p["name"] in ("Preston", "Lancaster", "Blackburn", "Clitheroe", "Blackpool")])),
                   "w": float(np.mean([p["w"] for p in R["uk_places"] if p["name"] in ("Preston", "Lancaster", "Blackburn", "Clitheroe", "Blackpool")]))}
# nearest ground from Lancashire (Preston) where both models put the base of the lithosphere below 200 km
deep = (L18 > 200) & (WG > 200)
dk = hav_km(53.763, -2.703, LA[deep], LO[deep]); i = int(np.argmin(dk))
cty = CTRY[deep][i]
R["lancashire"]["nearest_deep"] = {"km": float(dk[i]), "lat": float(LA[deep][i]), "lon": float(LO[deep][i]), "country": cnames[cty][1] if cty >= 0 else None}
gb = CTRY == [c[0] for c in cnames].index("GBR")
R["uk"]["l_range"] = [float(L18[gb].min()), float(L18[gb].max())]; R["uk"]["w_range"] = [float(WG[gb].min()), float(WG[gb].max())]
R["uk"]["crust_mean"] = uk["crust_mean"]


# volcanoes and diamond sites from Wikidata (QLever TSV)
def tsv(name):
    S = jload(f"{RAW}/litho_sink_20261029.json.gz")["qlever_tsv"][name].strip().split("\n")
    hdr = [h.lstrip("?") for h in S[0].split("\t")]
    out = []
    for line in S[1:]:
        p = line.split("\t"); r = dict(zip(hdr, p + [""] * (len(hdr) - len(p))))
        m = re.match(r"POINT\(([-\d.eE]+) ([-\d.eE]+)\)", r.get("coord", ""))
        if not m:
            continue
        r["lon"], r["lat"] = float(m.group(1)), float(m.group(2))
        for k in list(r):
            if isinstance(r[k], str):
                r[k] = re.sub(r'^"(.*)"(@\w+|\^\^.*)?$', r"\1", r[k]).replace("<http://www.wikidata.org/entity/", "").rstrip(">")
                r[k] = r[k].replace("\u2013", "-").replace("\u2014", "-")  # house style: no en or em dashes in names
        out.append(r)
    return out


def dedupe(rows, key):
    seen = {}
    for r in rows:
        if r[key] not in seen and -90 <= r["lat"] <= 90:
            seen[r[key]] = r
    return list(seen.values())


V = dedupe(tsv("volcanoes"), "v"); D = dedupe(tsv("diamonds"), "m")
for X in (V, D):
    la_ = np.array([r["lat"] for r in X]); lo_ = np.array([r["lon"] for r in X])
    a, b = sample(L18, la_, lo_), sample(WG, la_, lo_)
    iy = ((90 - la_) / RES).astype(int).clip(0, NY - 1); ix = ((lo_ + 180) / RES).astype(int) % NX
    for r, x, y, oc in zip(X, a, b, OCEAN[iy, ix]):
        r["l"], r["w"], r["a"], r["ocean"] = float(x), float(y), float((x + y) / 2), bool(oc)
with open(f"{DATA}/volcanoes.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["wikidata", "name", "gvp_number", "lat", "lon", "elevation_m", "on_oceanic_crust", "lithoref18_km", "winterc_km", "average_km"])
    for r in V:
        w.writerow([r["v"], r["vL"], r["gvp"], r["lat"], r["lon"], r.get("elev", ""), int(r["ocean"]), round(r["l"], 1), round(r["w"], 1), round(r["a"], 1)])
with open(f"{DATA}/diamond_sites.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["wikidata", "name", "lat", "lon", "lithoref18_km", "winterc_km", "average_km"])
    for r in D:
        w.writerow([r["m"], r["mL"], r["lat"], r["lon"], round(r["l"], 1), round(r["w"], 1), round(r["a"], 1)])


def pct_cont_thinner(x):
    return float(Wt[CONT & (AVG < x)].sum() / Wt[CONT].sum())


va = np.array([r["a"] for r in V]); da = np.array([r["a"] for r in D])
vc = np.array([r["a"] for r in V if not r["ocean"]])
R["volcanoes"] = {"n": len(V), "n_ocean": int(sum(r["ocean"] for r in V)), "median_a": float(np.median(va)), "median_a_continental": float(np.median(vc)),
                  "share_under_100": float((va < 100).mean()), "share_over_200": float((va > 200).mean()),
                  "share_cont_under_100": float((vc < 100).mean()),
                  "median_l": float(np.median([r["l"] for r in V])), "median_w": float(np.median([r["w"] for r in V]))}
R["diamonds"] = {"n": len(D), "median_a": float(np.median(da)), "median_l": float(np.median([r["l"] for r in D])), "median_w": float(np.median([r["w"] for r in D])),
                 "share_over_150": float((da > 150).mean()), "share_under_100": float((da < 100).mean()),
                 "cont_share_thinner_than_median": pct_cont_thinner(float(np.median(da))),
                 "thinnest": sorted([{"name": r["mL"], "a": r["a"], "lat": r["lat"], "lon": r["lon"]} for r in D], key=lambda r: r["a"])[:5]}
R["continent_median_a"] = R["models"]["average"]["continent"]["median"]

# Crameri / Conrad comparison is visual only: no numbers are taken from the images.
R["meta"]["retrieved"] = "29 October 2026"
jsave(R, f"{DATA}/results.json")

# page data: points for layers and search
jsave({"cities": [[c["name"], c["cc"], round(c["lat"], 3), round(c["lon"], 3), c["pop"]] for c in sorted(cities, key=lambda c: -c["pop"])],
       "cc": {k: v for k, v in ccn.items()},
       "volcanoes": [[r["vL"], round(r["lat"], 3), round(r["lon"], 3), round(r["a"])] for r in V],
       "diamonds": [[r["mL"], round(r["lat"], 3), round(r["lon"], 3), round(r["a"])] for r in D],
       "countries": [n for _, n in cnames], "plates": [n for _, n in pnames]}, f"{WORK}/points.json", compact=True)
print(json.dumps({k: R[k] for k in ("meta", "agree", "ocean_fit", "ridge", "cratons_summary", "uk", "lancashire", "volcanoes", "diamonds", "big_cities")}, indent=1)[:6000])
for k in ("lithoref18", "winterc", "average"):
    print(k, {z: {q: round(v, 3) for q, v in R["models"][k][z].items()} for z in ("all", "continent", "ocean")}, R["models"][k].get("max"), R["models"][k].get("min"))
