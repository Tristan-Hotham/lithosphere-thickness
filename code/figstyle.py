"""House style for static figures: fonts (static instances cut from the variable Fraunces and Source Serif 4 fonts in
~/.fonts, written to WORK), colours, colour maps, and Equal Earth raster maps drawn from the 0.25 degree grids."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont("/root/.fonts/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
    instancer.instantiateVariableFont(TTFont("/root/.fonts/Fraunces%5BSOFT,WONK,opsz,wght%5D.ttf"), {"wght": 600, "opsz": 48, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Semibold.ttf")
    for w, n in ((400, "Regular"), (600, "Semibold")):
        instancer.instantiateVariableFont(TTFont("/root/.fonts/SourceSerif4%5Bopsz,wght%5D.ttf"), {"wght": w, "opsz": 12}).save(f"{FD}/SourceSerif4-{n}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISP6 = fm.FontProperties(fname=f"{FD}/Fraunces-Semibold.ttf")
SERP = fm.FontProperties(fname=f"{FD}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FD}/SourceSerif4-Semibold.ttf")
fm.fontManager.addfont("/root/.fonts/IBMPlexMono-Regular.ttf")
fm.fontManager.addfont("/root/.fonts/IBMPlexMono-Medium.ttf")
MONO = "IBM Plex Mono"
BG, FG, MUT, RULE = "#F5F2EF", "#1F1A26", "#665E6C", "#DCD3CF"
HOT, DEEP, COOL, SAND = "#B5446E", "#3D2A57", "#2F6E8C", "#D9B88A"
VOLC, DIAM, PLATE = "#C92A2A", "#1C7ED6", "#E8590C"
plt.rcParams.update({"font.family": MONO, "font.size": 13, "axes.edgecolor": MUT, "axes.labelcolor": FG,
                     "xtick.color": MUT, "ytick.color": MUT, "text.color": FG, "axes.facecolor": BG, "figure.facecolor": BG,
                     "savefig.facecolor": BG})
ACTON = ListedColormap(load_cmap("acton")[::-1], name="acton_r")
VIK = ListedColormap(load_cmap("vik"), name="vik")
BATLOW = ListedColormap(load_cmap("batlow"), name="batlow")

EE = Transformer.from_crs(4326, 8857, always_xy=True)
EEi = Transformer.from_crs(8857, 4326, always_xy=True)
XMAX = EE.transform(180, 0)[0]; YMAX = EE.transform(0, 90)[1]


def ee_raster(grid, width=1600, extent=None, res=RES):
    """Resample a global cell-centred grid (row 0 at 90N) onto an Equal Earth image. Returns (img, extent)."""
    x0, x1, y0, y1 = extent or (-XMAX, XMAX, -YMAX, YMAX)
    h = int(round(width * (y1 - y0) / (x1 - x0)))
    xs = np.linspace(x0, x1, width); ys = np.linspace(y1, y0, h)
    X, Y = np.meshgrid(xs, ys)
    lon, lat = EEi.transform(X.ravel(), Y.ravel())
    lon = np.asarray(lon); lat = np.asarray(lat)
    ok = np.isfinite(lon) & np.isfinite(lat) & (np.abs(lon) <= 180.0001)
    # reject points outside the Equal Earth outline (the inverse can wrap)
    fx, fy = EE.transform(np.where(ok, lon, 0), np.where(ok, lat, 0))
    ok &= (np.abs(np.asarray(fx) - X.ravel()) < 1000) & (np.abs(np.asarray(fy) - Y.ravel()) < 1000)
    v = np.full(lon.shape, np.nan)
    ny, nx = grid.shape
    iy = ((90 - lat[ok]) / res).astype(int).clip(0, ny - 1); ix = ((lon[ok] + 180) / res).astype(int) % nx
    v[ok] = grid[iy, ix]
    return v.reshape(h, width), (x0, x1, y0, y1)


def ee_lines(ax, rings, **kw):
    for ring in rings:
        a = np.array(ring)
        if len(a) < 2:
            continue
        x, y = EE.transform(np.clip(a[:, 0], -179.99, 179.99), a[:, 1])
        x = np.asarray(x); y = np.asarray(y)
        br = np.where(np.abs(np.diff(a[:, 0])) > 180)[0]
        for seg in np.split(np.arange(len(a)), br + 1):
            if len(seg) > 1:
                ax.plot(x[seg], y[seg], **kw)


def ee_outline(ax, **kw):
    lat = np.linspace(-90, 90, 181)
    x1, y1 = EE.transform(np.full_like(lat, 180), lat); x2, y2 = EE.transform(np.full_like(lat, -180), lat[::-1])
    ax.plot(np.r_[x1, x2, x1[:1]], np.r_[y1, y2, y1[:1]], **kw)


def world_rings():
    return jload(f"{DATA}/world.json")["rings"]


def plate_lines():
    return [l["c"] for l in jload(f"{DATA}/boundaries.json")["lines"]]


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
