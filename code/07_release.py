"""Step 7. Blog post (release/blog/post.html, meta.json), Zenodo folder (release/zenodo/), README.md and LICENSE."""
import re, shutil, zipfile, glob
from common import *
import importlib.util

spec = importlib.util.spec_from_file_location("bs", os.path.join(HERE, "04_build_site.py")); bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
R = bs.R; fill = bs.fill
BLOG = os.path.join(ROOT, "release", "blog"); ZEN = os.path.join(ROOT, "release", "zenodo")
os.makedirs(BLOG, exist_ok=True); os.makedirs(ZEN, exist_ok=True)
TITLE = "How Thick Is the Ground Beneath You? Lithosphere Thickness from Two Open Global Models"
PDF = "Hotham_Lithosphere_Thickness.pdf"

# blog
post = fill(open(os.path.join(HERE, "blog_template.html"), encoding="utf-8").read())
assert "{{" not in post.replace("{{IMG|", "")
for m in re.findall(r"\{\{IMG\|([^|]+)\|", post):
    assert os.path.exists(os.path.join(BLOG, m)), m
open(os.path.join(BLOG, "post.html"), "w", encoding="utf-8").write(post)
txt = re.sub(r"<[^>]+>", " ", re.sub(r"\{\{IMG\|[^}]*\}\}", " ", post))
print("blog words", len(txt.split()))
jsave({"title": "How thick is the ground beneath you?", "slug": "lithosphere-thickness",
       "excerpt": f"The Earth's rigid shell averages about {R['models']['average']['all']['mean']:.0f} km thick, from {R['ridge']['lithoref18_median_young']:.0f} km at the mid-ocean ridges to more than 200 km under the oldest continents. I mapped it everywhere from two open models, with volcanoes, diamonds and Lancashire.",
       "seo_description": "An interactive world map of lithosphere thickness from two open models, with sea-floor age, plates, volcanoes and diamond mines.",
       "tags": ["geology", "plate tectonics", "lithosphere", "maps", "data visualisation", "open data", "earth science", "diamonds"],
       "header_alt": "World map of lithosphere thickness in pinks and deep purples with orange plate boundaries, beside the title How thick is the ground beneath you?"},
      os.path.join(BLOG, "meta.json"))

# LICENSE and README
open(os.path.join(ROOT, "LICENSE"), "w").write("""Code (everything in code/ and reddit/collage.py): MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text, figures and derived data: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0),
https://creativecommons.org/licenses/by-sa/4.0/ . The page reproduces a CC BY-SA 4.0 graphic by Fabio Crameri (s-Ink).
Source models and data keep their own licences: LithoRef18 via EarthByte (CC BY 4.0), WINTERC-G (CC BY 4.0),
Seton et al. 2020 age grid via EarthByte (CC BY 4.0), PB2002 GeoJSON (ODC-BY 1.0), Wikidata (CC0), GeoNames (CC BY 4.0),
Natural Earth (public domain), Scientific colour maps (MIT). See README.md.
""")
readme = fill(open(os.path.join(HERE, "readme_template.md"), encoding="utf-8").read())
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, ".gitignore"), "w").write("__pycache__/\n*.pyc\n")

# Zenodo folder
for f in glob.glob(os.path.join(ZEN, "*")):
    os.remove(f)
shutil.copy(os.path.join(ROOT, "release", PDF), ZEN)
for f in ("lithoref18_2deg.csv", "winterc_g_lab_points.csv", "countries.csv", "cities.csv", "volcanoes.csv", "diamond_sites.csv", "ocean_thickness_by_age.csv", "plates.csv"):
    shutil.copy(os.path.join(DATA, f), ZEN)
with zipfile.ZipFile(os.path.join(ZEN, "lithosphere-thickness_code_and_data.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    for base in ("code", "data"):
        for f in sorted(glob.glob(os.path.join(ROOT, base, "**", "*"), recursive=True)):
            if os.path.isfile(f) and "__pycache__" not in f:
                z.write(f, os.path.relpath(f, ROOT))
    for f in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, f), f)
abstract = open(os.path.join(HERE, "paper_template.tex"), encoding="utf-8").read()
abstract = abstract.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
abstract = bs.fill(abstract).replace("\\%", "%").replace("\\textsuperscript{2}", "²")
jsave({"title": TITLE,
       "description_html": f"<p>{abstract}</p><p>Interactive version: {SITE_URL}. Data and code: {REPO_URL}. Blog post: to follow.</p>",
       "keywords": ["lithosphere", "lithosphere-asthenosphere boundary", "plate tectonics", "cratons", "oceanic lithosphere", "sea-floor age", "diamonds", "volcanoes", "open data", "interactive map"],
       "licence": "cc-by-sa-4.0",
       "related": [{"identifier": REPO_URL, "relation": "issupplementedby", "resource_type": "software"},
                   {"identifier": SITE_URL, "relation": "issupplementedby", "resource_type": "other"},
                   {"identifier": "https://doi.org/10.1093/gji/ggz094", "relation": "isderivedfrom", "resource_type": "other"},
                   {"identifier": "https://www.earthbyte.org/webdav/ftp/earthbyte/gplates_portal/Afonso_etal_lithospheric_thickness_GJI2019/", "relation": "isderivedfrom", "resource_type": "dataset"},
                   {"identifier": "https://doi.org/10.5281/zenodo.5771863", "relation": "isderivedfrom", "resource_type": "dataset"},
                   {"identifier": "https://doi.org/10.1029/2020GC009214", "relation": "isderivedfrom", "resource_type": "dataset"},
                   {"identifier": "https://github.com/fraxen/tectonicplates", "relation": "isderivedfrom", "resource_type": "dataset"},
                   {"identifier": "https://s-ink.org/lithosphere-thickness-map", "relation": "isderivedfrom", "resource_type": "other"},
                   {"identifier": "https://www.wikidata.org/", "relation": "isderivedfrom", "resource_type": "dataset"}]},
      os.path.join(ZEN, "meta.json"))
for f in sorted(os.listdir(ZEN)):
    print(f, os.path.getsize(os.path.join(ZEN, f)))
