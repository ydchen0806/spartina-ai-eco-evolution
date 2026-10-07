## recommend to create a virtual environment to run this python script

"""
Train RF on GSM_boundary_2023_clipped.tif using training polygons,
then APPLY model to full NAIP GSM_20230811.tif, clipped to GSM_boundary_2015.shp,
then EXCLUDE GSM_boundary_2015_forest.shp (set to nodata=0),
and SAVE an AOI-only classified GeoTIFF.
"""

import os
import random
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.mask import mask
from rasterio.features import geometry_mask
from shapely.ops import unary_union
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    cohen_kappa_score
)
import matplotlib.pyplot as plt

# ----------------------------
# Reproducibility
# ----------------------------
random.seed(42)
np.random.seed(42)

# ----------------------------
# PATHS
# ----------------------------
# Training raster (covers training polygons well)
train_raster_path = r"~/P.australis_expansion/GSM_boundary_2023_clipped.tif"

# Full NAIP raster to APPLY model on
apply_raster_path = r"~/P.australis_expansion/GSM_20230811.tif"

# Training polygons
training_shp_path = r"~/P.australis_expansion/GSM_training_data_2023.shp"
label_col = "id"  # class code column

# AOI 2015 and forest exclusion
aoi_2015_shp = r"~/P.australis_expansion/GSM_boundary_2015.shp"
forest_exclusion_shp = r"~/P.australis_expansion/GSM_boundary_2015_forest.shp"

# Output products
out_dir = r"~/P.australis_expansion/output"
os.makedirs(out_dir, exist_ok=True)

out_classified_path = os.path.join(out_dir, "GSM_2023_RF_classified_AOI2015_minus_forest.tif")

# ----------------------------
# 1) TRAIN MODEL on training raster + polygons
# ----------------------------
with rasterio.open(train_raster_path) as train_src:
    training_gdf = gpd.read_file(training_shp_path).to_crs(train_src.crs)

    labels = []
    samples = []

    for _, row in training_gdf.iterrows():
        geom = [row.geometry]
        label = row[label_col]

        chip, _ = mask(train_src, geom, crop=True)  # (bands, r, c)

        # valid pixels inside chip
        if train_src.nodata is not None:
            valid_mask = chip[0] != train_src.nodata
        else:
            valid_mask = np.any(chip != 0, axis=0)

        pix = chip[:, valid_mask].T  # (n_pixels, n_bands)
        if pix.size == 0:
            continue

        samples.append(pix)
        labels.extend([label] * pix.shape[0])

X = np.vstack(samples)
y = np.array(labels)

# Train/test split (pixel-level holdout)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

print("\n=== Classification report (holdout pixels) ===")
print(classification_report(y_test, y_pred))

kappa = cohen_kappa_score(y_test, y_pred)
print(f"Cohen's Kappa: {kappa:.3f}")

# ----------------------------
# 2) APPLY MODEL on full NAIP, clipped to AOI 2015, excluding forest polygons
# ----------------------------
with rasterio.open(apply_raster_path) as src_img:
    # Read AOI + forest, reproject to NAIP CRS
    aoi = gpd.read_file(aoi_2015_shp).to_crs(src_img.crs)
    forest = gpd.read_file(forest_exclusion_shp).to_crs(src_img.crs)

    aoi_geom = unary_union(aoi.geometry)
    forest_geom = unary_union(forest.geometry) if len(forest) > 0 else None

    # Clip multiband NAIP to AOI (crop=True)
    img_clip, transform_clip = mask(src_img, [aoi_geom], crop=True)
    meta = src_img.meta.copy()

bands, rows, cols = img_clip.shape

# Build valid mask in clipped NAIP
# NAIP often has no nodata; this catches all-zero edge pixels if present
if meta.get("nodata") is not None:
    nodata_val = meta["nodata"]
    valid_mask = img_clip[0] != nodata_val
else:
    valid_mask = np.any(img_clip != 0, axis=0)

# Build forest exclusion mask in CLIPPED grid
if forest_geom is not None and (not forest_geom.is_empty):
    forest_mask = geometry_mask(
        [forest_geom],
        out_shape=(rows, cols),
        transform=transform_clip,
        invert=True  # True = inside forest polygons
    )
else:
    forest_mask = np.zeros((rows, cols), dtype=bool)

# Predict only where valid and NOT forest
predict_mask = valid_mask & (~forest_mask)

X_all = img_clip.reshape(bands, -1).T  # (n_pixels, n_bands)
pred_flat = np.zeros(X_all.shape[0], dtype=np.uint8)  # 0 = nodata outside AOI/forest/invalid

idx = np.where(predict_mask.ravel())[0]
pred_flat[idx] = clf.predict(X_all[idx]).astype(np.uint8)

classified_clip = pred_flat.reshape(rows, cols).astype(np.uint8)

# ----------------------------
# 3) SAVE OUTPUT
# ----------------------------
meta.update({
    "height": rows,
    "width": cols,
    "transform": transform_clip,
    "count": 1,
    "dtype": "uint8",
    "nodata": 0
})

with rasterio.open(out_classified_path, "w", **meta) as dst:
    dst.write(classified_clip, 1)

print("\nSaved classified raster (AOI2015, forest excluded):")
print(out_classified_path)
print("\n=== Script finished successfully ===")

"""
Generate stratified random validation points from:
GSM_2023_RF_classified_AOI2015_minus_forest.tif

- 50 points each for PA (1), LM (2), HM (3)
- Saves:
  1) GeoPackage with points (for QGIS overlay)
  2) Excel spreadsheet template for visual validation

How to fill Excel:
- If map_class matches what you see on NAIP: correct_01 = 1, leave ref_class blank
- If not: correct_01 = 0, fill ref_class with PA / LM / HM / Other / Unclear, plus notes if needed
"""

import os
import numpy as np
import pandas as pd
import rasterio
import geopandas as gpd
from shapely.geometry import Point

# ----------------------------
# USER SETTINGS
# ----------------------------
classified_raster = r"~/P.australis_expansion/output/GSM_2023_RF_classified_AOI2015_minus_forest.tif"

out_dir = r"~/P.australis_expansion/output"
os.makedirs(out_dir, exist_ok=True)

n_per_class = 50
seed = 42

# Class IDs in your map
class_map = {1: "PA", 2: "LM", 3: "HM"}  # ONLY sampling these

out_gpkg = os.path.join(out_dir, "GSM_validation_points_150_AOI2015_minus_forest.gpkg")
out_xlsx = os.path.join(out_dir, "GSM_validation_points_150_AOI2015_minus_forest.xlsx")

# ----------------------------
# LOAD RASTER + SAMPLE POINTS
# ----------------------------
rng = np.random.default_rng(seed)

with rasterio.open(classified_raster) as src:
    cls = src.read(1)
    transform = src.transform
    crs = src.crs
    nodata = src.nodata if src.nodata is not None else 0

# valid pixels (inside AOI and not forest, because you set forest/outside to 0)
valid = cls != nodata

records = []
geoms = []
point_id = 1

for cid, cname in class_map.items():
    rr, cc = np.where((cls == cid) & valid)

    if len(rr) < n_per_class:
        raise ValueError(
            f"Not enough pixels for {cname} (class {cid}). "
            f"Have {len(rr)}, need {n_per_class}. "
            "Check your classified raster or class codes."
        )

    pick = rng.choice(len(rr), size=n_per_class, replace=False)
    rr = rr[pick]
    cc = cc[pick]

    for r, c in zip(rr, cc):
        x, y = rasterio.transform.xy(transform, r, c, offset="center")
        records.append({
            "point_id": point_id,
            "map_class_id": cid,
            "map_class": cname,
            "correct_01": "",   # you fill: 1 or 0
            "ref_class": "",    # you fill ONLY if incorrect: PA/LM/HM/Other/Unclear
            "notes": "",
            "x": x,
            "y": y
        })
        geoms.append(Point(x, y))
        point_id += 1

gdf = gpd.GeoDataFrame(records, geometry=geoms, crs=crs)

# Add lon/lat helper columns (WGS84) for easier navigation if needed
try:
    gdf_wgs84 = gdf.to_crs(epsg=4326)
    gdf["lon"] = gdf_wgs84.geometry.x
    gdf["lat"] = gdf_wgs84.geometry.y
except Exception:
    gdf["lon"] = np.nan
    gdf["lat"] = np.nan

# ----------------------------
# SAVE OUTPUTS
# ----------------------------
# GeoPackage for QGIS
gdf.to_file(out_gpkg, layer="validation_points", driver="GPKG")

# Excel template (no geometry column)
pd.DataFrame(gdf.drop(columns="geometry")).to_excel(out_xlsx, index=False)

print("Created validation outputs:")
print(" - GeoPackage (load in QGIS):", out_gpkg)
print(" - Excel template (fill for validation):", out_xlsx)

print("\nExcel instructions:")
print(" - correct_01 = 1 if map_class matches NAIP; leave ref_class blank")
print(" - correct_01 = 0 if not; fill ref_class as PA/LM/HM/Other/Unclear")
print(" - optional: add notes")

# adjusted area (Olofsson-style) for PA/LM/HM

import numpy as np
import pandas as pd
import rasterio

# ----------------------------
# USER SETTINGS
# ----------------------------
classified_raster = r"~/P.australis_expansion/output/GSM_2023_RF_classified_AOI2015_minus_forest.tif"
validation_xlsx   = r"~/P.australis_expansion/output/GSM_validation_points_150_AOI2015_minus_forest.xlsx"

# target classes
classes = ["PA", "LM", "HM"]
other_label = "OTHER"

# class IDs in raster
id_to_name = {1: "PA", 2: "LM", 3: "HM"}

# ----------------------------
# 1) MAPPED AREAS (pixel count) WITHIN CLIPPED RASTER
# ----------------------------
with rasterio.open(classified_raster) as src:
    cls = src.read(1)
    nodata = src.nodata if src.nodata is not None else 0
    valid = cls != nodata
    pixel_area = abs(src.transform.a * src.transform.e)

A_map = {}
for cid, cname in id_to_name.items():
    A_map[cname] = np.sum((cls == cid) & valid) * pixel_area

A_domain = sum(A_map[c] for c in classes)
if A_domain <= 0:
    raise ValueError("A_domain is 0. Check class codes or that your raster is clipped correctly.")

W = {c: A_map[c] / A_domain for c in classes}

print("\n=== Pixel-count mapped areas (AOI2015 minus forest) ===")
for c in classes:
    print(f"{c}: {A_map[c]:,.2f} m^2")
print(f"Domain (PA+LM+HM): {A_domain:,.2f} m^2")
print("Weights W:", W)

# ----------------------------
# 2) LOAD VALIDATION SHEET + BUILD REFERENCE LABELS
# ----------------------------
df = pd.read_excel(validation_xlsx)

# normalize text
df["map_class"] = df["map_class"].astype("string").str.strip().str.upper()
df["ref_class"] = df["ref_class"].astype("string").str.strip().str.upper()
df["correct_01"] = pd.to_numeric(df["correct_01"], errors="coerce")

# if correct_01==1 and ref_class blank -> set ref_class = map_class
mask_fill = (df["correct_01"] == 1) & (df["ref_class"].isna() | (df["ref_class"] == ""))
df.loc[mask_fill, "ref_class"] = df.loc[mask_fill, "map_class"]

# warn if incorrect but ref_class missing
mask_bad = (df["correct_01"] == 0) & (df["ref_class"].isna() | (df["ref_class"] == ""))
if mask_bad.any():
    print("\nWARNING: Some incorrect points are missing ref_class. Fix these rows:")
    print(df.loc[mask_bad, ["point_id","map_class","correct_01","ref_class"]].head(30))
    raise ValueError("Stop: fill ref_class for incorrect points, then rerun.")

# collapse any non-PA/LM/HM to OTHER
df.loc[~df["map_class"].isin(classes), "map_class"] = other_label
df.loc[~df["ref_class"].isin(classes), "ref_class"] = other_label

# keep only sampled strata (PA/LM/HM)
df = df[df["map_class"].isin(classes)].copy()

# ----------------------------
# 3) CONFUSION COUNTS n_ij (rows=MAP strata i, cols=REFERENCE j)
# ----------------------------
ref_levels = classes + [other_label]
map_levels = classes

n = np.zeros((len(map_levels), len(ref_levels)), dtype=int)

for i, mc in enumerate(map_levels):
    sub = df[df["map_class"] == mc]
    for j, rc in enumerate(ref_levels):
        n[i, j] = np.sum(sub["ref_class"] == rc)

n_i = n.sum(axis=1)

print("\n=== Confusion counts (rows=map strata, cols=reference) ===")
print(pd.DataFrame(n, index=map_levels, columns=ref_levels))
print("Row totals (should be 50 each):", n_i)

# proportions within each map stratum
p_ij = np.divide(n, n_i[:, None], where=(n_i[:, None] != 0))

# ----------------------------
# 4) ADJUSTED AREA ESTIMATES (Olofsson-style)
# p_plus_j = Σ_i W_i * p_ij
# A_hat_j = A_domain * p_plus_j
# ----------------------------
p_plus = np.zeros(len(ref_levels), dtype=float)
for i, mc in enumerate(map_levels):
    p_plus += W[mc] * p_ij[i, :]

A_hat = A_domain * p_plus

# ----------------------------
# 5) SE + 95% CI (approx stratified; no finite pop correction)
# Var(p_plus_j) = Σ_i W_i^2 * [p_ij(1-p_ij)/(n_i-1)]
# ----------------------------
var_p_plus = np.zeros(len(ref_levels), dtype=float)

for j in range(len(ref_levels)):
    s = 0.0
    for i, mc in enumerate(map_levels):
        ni = n_i[i]
        if ni <= 1:
            continue
        pij = p_ij[i, j]
        var_pij = (pij * (1 - pij)) / (ni - 1)
        s += (W[mc] ** 2) * var_pij
    var_p_plus[j] = s

se_A = A_domain * np.sqrt(var_p_plus)
ci_low = A_hat - 1.96 * se_A
ci_high = A_hat + 1.96 * se_A

# ----------------------------
# 6) OUTPUT
# ----------------------------
out = pd.DataFrame({
    "class": ref_levels,
    "mapped_area_m2": [A_map.get(c, np.nan) for c in ref_levels],
    "adjusted_area_m2": A_hat,
    "SE_m2": se_A,
    "CI95_low_m2": ci_low,
    "CI95_high_m2": ci_high
})

print("\n=== Adjusted area estimates (AOI2015 minus forest; PA/LM/HM domain) ===")
print(out[out["class"].isin(classes)][["class","mapped_area_m2","adjusted_area_m2","SE_m2","CI95_low_m2","CI95_high_m2"]])

out_csv = validation_xlsx.replace(".xlsx", "_ADJUSTED_AREA_RESULTS.csv")
out.to_csv(out_csv, index=False)
print("\nSaved results:", out_csv)
