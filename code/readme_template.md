# How thick is the ground beneath you?

An interactive world map of lithosphere thickness: how far down the base of the Earth's rigid outer shell lies beneath every place, from two open global models (LithoRef18 and WINTERC-G), with sea-floor ages, plate boundaries, volcanoes and diamond mines. Click anywhere for a cross-section of the ground beneath it.

**Interactive version:** https://maps.tristanhotham.com/lithosphere-thickness/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23782261

**Blog post:** https://blog.tristanhotham.com/2026/10/29/lithosphere-thickness/

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Why two models, not the s-Ink map

The study started from Fabio Crameri's map on s-Ink (https://s-ink.org/lithosphere-thickness-map), drawn from the model of Conrad and Lithgow-Bertelloni (2006). The s-Ink download (LithosphereThickness.zip) holds 24 PNG images and a readme, but no gridded values, and I could not find an open copy of that grid. Rather than digitise colours from an image, I used two newer models that publish their numbers under open licences. Crameri's image is reproduced on the page, with credit, for comparison only.

## Headline results

- Both models give the same area-weighted global mean thickness: {{models.lithoref18.all.mean|f1}} km (LithoRef18) and {{models.winterc.all.mean|f1}} km (WINTERC-G). Continental median {{models.average.continent.median|int}} km, oceanic median {{models.average.ocean.median|int}} km (mean of the two models).
- They correlate cell by cell at r = {{agree.r_all|f2}}, with a median absolute difference of {{agree.median_absdiff|int}} km; they differ by more than 50 km over {{agree.share_diff_over_50|pct}} of the surface, most of all under the East European Platform and Tibet (WINTERC-G {{contrasts.3.w|int}} km, LithoRef18 {{contrasts.3.l|int}} km at the Tibet point).
- Ocean lithosphere thickens with age: in LithoRef18 from a median of {{ridge.lithoref18_median_young|int}} km on sea floor under 2 million years old to {{ridge.lithoref18_median_old|int}} km on sea floor over 150 million years (correlation with the square root of age r = {{ocean_fit.lithoref18.r_sqrt_age_all_ocean|f2}}); WINTERC-G from {{ridge.winterc_median_young|int}} to {{ridge.winterc_median_old|int}} km.
- At {{cratons_summary.n|int}} craton points the median is {{cratons_summary.median_l|int}} km (LithoRef18) and {{cratons_summary.median_w|int}} km (WINTERC-G); the eastern North China craton point has only {{cratons.13.a|int}} km.
- {{volcanoes.share_under_100|pct}} of {{volcanoes.n|int}} volcanoes (Wikidata items with a Global Volcanism Program number) stand on lithosphere thinner than 100 km. {{diamonds.share_over_150|pct}} of {{diamonds.n|int}} diamond mines in Wikidata sit on lithosphere thicker than 150 km; their median, {{diamonds.median_a|int}} km, is deeper than {{diamonds.cont_share_thinner_than_median|pct}} of continental ground.
- The UK averages {{uk.country.average_mean|int}} km, {{uk.rank_thickest|ord}} thickest of {{countries.n_big|int}} countries. Under Lancashire the base lies about {{lancashire.l|int}} km (LithoRef18) or {{lancashire.w|int}} km (WINTERC-G) down; the nearest ground where both models exceed 200 km is in {{lancashire.nearest_deep.country}}, about {{lancashire.nearest_deep.km|r10}} km from Preston.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (results embedded; grids and points loaded from `data/`). |
| `header.png` | Social card (1200 by 630). |
| `data/results.json` | Every number used anywhere. |
| `data/lithoref18_2deg.csv` | LithoRef18 at its {{meta.lithoref18_points|int}} cells of 2 degrees: elevation, Moho and lithosphere base depths, crust and lithosphere thickness. |
| `data/winterc_g_lab_points.csv` | WINTERC-G thermal lithosphere base depth at its {{meta.winterc_nodes|int}} nodes. |
| `data/countries.csv` | Area-weighted means by country (both models, mean, crust). |
| `data/plates.csv` | Area-weighted means by PB2002 plate. |
| `data/cities.csv` | GeoNames places of 100,000 or more ({{meta.cities_page|int}}) with both models' values. |
| `data/volcanoes.csv`, `data/diamond_sites.csv` | Wikidata points with sampled thickness. |
| `data/ocean_thickness_by_age.csv` | Ocean thickness by sea-floor age band. |
| `data/grid_a.png`, `data/grid_b.png` | Page grids, 1440 by 720 cells of 0.25 degrees (row 0 at 90N, column 0 at 180W). grid_a: red = LithoRef18 and green = WINTERC-G thickness, code = km / 1.25 + 1; blue = sea-floor age, code = Myr / 1.4 + 1, 0 = no oceanic crust. grid_b: red = plate index + 1, green = country index + 1, blue = LithoRef18 crust km + 1 (names in `points.json`). |
| `data/points.json` | Page lists: cities, volcanoes, diamond mines, country and plate names, area distribution of thickness. |
| `data/boundaries.json`, `data/world.json` | PB2002 plate boundaries; simplified Natural Earth outlines. |
| `data/crameri_lithosphere_thickness.jpg` | Fabio Crameri's s-Ink map, reduced (CC BY-SA 4.0). |
| `code/` | Analysis, page, figures, paper and release scripts (see below); `code/cmaps/` holds four Scientific colour maps. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Thickness.** LithoRef18: depth of the lithosphere base below the surface (base depth minus elevation), 2 degree cells, bilinearly interpolated to 0.25 degrees. WINTERC-G: depth of the thermal base of the lithosphere at nodes about 225 km apart, inverse-distance interpolated (four nearest nodes) to 0.25 degrees; range 45 to 300 km, {{models.winterc.max.n_at_max|int}} nodes at the 300 km ceiling. Default map: mean of the two.
- **Sea floor.** Seton et al. (2020) age grid, 6 arc-minutes, averaged into 0.25 degree cells; cells without oceanic crust count as continental (includes shelves).
- **Areas.** All shares weighted by cell area. Country and plate means over cells whose centres fall in each polygon; countries with at least 20,000 km² in the grid.
- **Points.** Sampled bilinearly. Craton points are approximate centres chosen from general geological maps.

## Known limits

- The base of the lithosphere is not a sharp surface; both models use thermal definitions. Read values as estimates with uncertainties of tens of kilometres.
- Both models are coarse; values at single towns are interpolations between a few model points.
- WINTERC-G is capped at 300 km and floored at 45 km.
- Wikidata lists of volcanoes and especially diamond mines ({{diamonds.n|int}}) are incomplete and uneven.
- The Conrad and Lithgow-Bertelloni grid was not available, so the comparison with the s-Ink map is visual only.

## Sources and licences

- LithoRef18: Afonso, J.C., Salajegheh, F., Szwillus, W., Ebbing, J. and Gaina, C. (2019) Geophysical Journal International 217(3): 1602 to 1628, https://doi.org/10.1093/gji/ggz094 . Source file from the EarthByte GPlates Portal, https://www.earthbyte.org/webdav/ftp/earthbyte/gplates_portal/Afonso_etal_lithospheric_thickness_GJI2019/ (EarthByte file area: CC BY 4.0).
- WINTERC-G: Fullea, J., Lebedev, S., Martinec, Z. and Celli, N.L. (2021) Geophysical Journal International 226(1): 146 to 191; model files v5.4, https://doi.org/10.5281/zenodo.5771863 (CC BY 4.0).
- Sea-floor age: Seton, M. et al. (2020) Geochemistry, Geophysics, Geosystems, https://doi.org/10.1029/2020GC009214 ; EarthByte age grid 2020.1 (CC BY 4.0).
- Plates: Bird, P. (2003) Geochemistry, Geophysics, Geosystems 4(3): 1027; GeoJSON by Hugo Ahlenius, Nordpil, https://github.com/fraxen/tectonicplates (ODC-BY 1.0).
- Original map: Fabio Crameri, s-Ink, https://s-ink.org/lithosphere-thickness-map , based on Conrad, C.P. and Lithgow-Bertelloni, C. (2006) Geophysical Research Letters 33: L05312, https://doi.org/10.1029/2005GL025621 (CC BY-SA 4.0).
- Colour maps: Crameri, F. Scientific colour maps, https://doi.org/10.5281/zenodo.1243862 (MIT licence), via the cmcrameri package.
- Volcanoes and diamond mines: Wikidata via QLever (CC0), retrieved {{meta.retrieved}}. Cities: GeoNames cities15000 (CC BY 4.0). Country outlines: Natural Earth (public domain).
- Base map tiles on the page © Esri and partners.

Text, figures and derived data: CC BY-SA 4.0 (the page reproduces a CC BY-SA 4.0 image). Code: MIT (see `LICENSE`).

## How to rerun

The raw downloads (two gzipped JSON bundles from EarthByte, Zenodo, s-Ink and QLever, retrieved {{meta.retrieved}}, plus the PB2002 GeoJSON and README from GitHub) are read in place from the folder in `code/common.py` (`LITHO_RAW`). Python 3 with numpy, scipy, h5py, matplotlib, Pillow, pyproj and fontTools; Playwright only for testing; xelatex for the paper.

```
python3 code/01_prepare.py      # grids on 0.25 degrees
python3 code/02_analyse.py      # all statistics, CSVs, results.json
python3 code/03_page_data.py    # page grids and point lists
python3 code/04_build_site.py   # index.html
python3 code/05_figures.py      # blog and paper figures, header.png
python3 code/06_paper.py        # paper PDF
python3 code/07_release.py      # blog post, metadata, Zenodo folder, this README
python3 reddit/collage.py       # collage
```

## Citation

Hotham, T. (2026) How thick is the ground beneath you? Lithosphere thickness from two open global models. https://doi.org/10.5281/zenodo.23782261

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
