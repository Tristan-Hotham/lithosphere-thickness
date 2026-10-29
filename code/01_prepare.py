"""Step 1. Read the downloaded bundles and build 0.25 degree global grids in WORK/grids.npz:
  litho18   LithoRef18 lithosphere thickness, km (surface to LAB), bilinear from the 2 degree model
  crust18   LithoRef18 crustal thickness, km (surface to Moho)
  elev18    LithoRef18 surface elevation, m
  winterc   WINTERC-G depth of the thermal LAB, km, inverse-distance from its triangular grid
  age       Seton et al. (2020) age of oceanic crust, Myr (NaN where there is no oceanic crust)
Also writes the raw LithoRef18 and WINTERC-G points to data/ as CSV for reuse.
"""
import io, csv
import numpy as np
import h5py
from scipy.spatial import cKDTree
from common import *

eb = jload(f"{RAW}/litho_earthbyte_20261029.json.gz")

# LithoRef18: 2 degree cell centres, lon -179..179, lat -89..89
rows = []
for line in eb["lithoref18_xyz"].splitlines():
    p = line.split()
    if len(p) == 14:
        try:
            rows.append([float(x) for x in p])
        except ValueError:
            pass
A = np.array(rows)
print("LithoRef18 points", len(A))
lon, lat, elev, moho, lab = A[:, 0], A[:, 1], A[:, 2], A[:, 3], A[:, 4]
thick = (elev - lab) / 1000.0           # km, surface to LAB (EarthByte: LAB minus ELEVATION, sign flipped)
crust = (elev - moho) / 1000.0
lons2 = np.arange(-179, 180, 2.0); lats2 = np.arange(89, -90, -2.0)
G18 = {k: np.full((90, 180), np.nan) for k in ("thick", "crust", "elev", "lab")}
ix = np.round((lon + 179) / 2).astype(int); iy = np.round((89 - lat) / 2).astype(int)
for k, v in (("thick", thick), ("crust", crust), ("elev", elev), ("lab", -lab / 1000.0)):
    G18[k][iy, ix] = v
assert not np.isnan(G18["thick"]).any()
with open(f"{DATA}/lithoref18_2deg.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["lon", "lat", "elevation_m", "moho_depth_km_bsl", "lab_depth_km_bsl", "crust_thickness_km", "lithosphere_thickness_km"])
    for i in range(len(A)):
        w.writerow([lon[i], lat[i], round(elev[i], 1), round(-moho[i] / 1000, 2), round(-lab[i] / 1000, 2), round(crust[i], 2), round(thick[i], 2)])


def up2(g):
    """Bilinear upsample of a 2 degree cell-centred grid to the 0.25 degree grid (periodic in longitude)."""
    LO, LA = np.meshgrid(LONS, LATS)
    return sample(g, LA, LO, res=2.0)


litho18 = up2(G18["thick"]); crust18 = up2(G18["crust"]); elev18 = up2(G18["elev"])

# WINTERC-G LAB on its triangular grid: column, lon (0..360), lat, LAB depth km
W = np.loadtxt(io.StringIO(eb["winterc_lab"]))
print("WINTERC-G points", len(W), "LAB range", W[:, 3].min(), W[:, 3].max())
wl = np.where(W[:, 1] > 180, W[:, 1] - 360, W[:, 1]); wa = W[:, 2]; wv = W[:, 3]
with open(f"{DATA}/winterc_g_lab_points.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["node", "lon", "lat", "lab_depth_km"])
    for r, lo_ in zip(W, wl):
        w.writerow([int(r[0]), round(lo_, 3), r[2], round(r[3], 2)])


def xyz(la, lo):
    la, lo = np.radians(la), np.radians(lo)
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])


tree = cKDTree(xyz(wa, wl))
LO, LA = np.meshgrid(LONS, LATS)
d, k = tree.query(xyz(LA.ravel(), LO.ravel()), k=4)
d = np.maximum(d, 1e-9); wt = 1 / d ** 2
winterc = ((wv[k] * wt).sum(1) / wt.sum(1)).reshape(NY, NX)
print("node spacing check: median nearest-node distance km", round(float(np.median(d[:, 0])) * 6371, 1))

# Seton et al. 2020 age grid, 6 arc-minute, gridline registered, NetCDF-4
open(f"{WORK}/age.nc", "wb").write(base64.b64decode(eb["agegrid_nc_b64"]))
with h5py.File(f"{WORK}/age.nc") as f:
    alon = f["lon"][:]; alat = f["lat"][:]; z = f["z"][:].astype(np.float32)
    fill = f["z"].attrs.get("_FillValue")
if fill is not None:
    z[z == np.float32(fill[0] if hasattr(fill, "__len__") else fill)] = np.nan
print("age grid", z.shape, "lat order", alat[0], alat[-1], "max age", np.nanmax(z))
# sample every 0.25 degree cell centre with the mean of the 6 arc-minute nodes inside it (NaN if under half are ocean)
ia = np.searchsorted(alat, LATS) if alat[0] < alat[-1] else None
age = np.full((NY, NX), np.nan, np.float32)
latn = alat if alat[0] < alat[-1] else alat[::-1]
zz = z if alat[0] < alat[-1] else z[::-1]
for j, la in enumerate(LATS):
    r = np.where(np.abs(latn - la) <= RES / 2)[0]
    blk = zz[r]                       # rows inside the cell band
    # columns: nodes at -180 + 0.1 i; cells of 0.25 contain 2 or 3 nodes
    cols = np.floor((alon + 180) / RES).astype(int).clip(0, NX - 1)
    s = np.zeros(NX); n = np.zeros(NX); c = np.zeros(NX)
    for row in blk:
        ok = ~np.isnan(row)
        np.add.at(s, cols[ok], row[ok]); np.add.at(n, cols[ok], 1); np.add.at(c, cols, 1)
    m = n >= c / 2
    age[j, m] = (s[m] / n[m])
print("ocean cells", int((~np.isnan(age)).sum()), "of", NX * NY)

np.savez_compressed(f"{WORK}/grids.npz", litho18=litho18.astype(np.float32), crust18=crust18.astype(np.float32),
                    elev18=elev18.astype(np.float32), winterc=winterc.astype(np.float32), age=age,
                    g18_thick=G18["thick"], g18_crust=G18["crust"], g18_elev=G18["elev"])
print("litho18 range", np.nanmin(litho18), np.nanmax(litho18), "winterc range", winterc.min(), winterc.max())
