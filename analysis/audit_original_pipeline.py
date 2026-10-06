#!/usr/bin/env python3
"""Audit the recovered upstream AI4FastEvolution input archive.

The upstream public repository contains the patch-size/position matrices and
the weather table used to construct the 854-row environment-growth workbook.
This script verifies that link and inventories the image dates referenced by
the matrices. It does not claim that the referenced TIFF/JPEG files are
bundled with this release. Local imagery, masks and annotations were recovered
on 2026-10-06; see docs/RECOVERY_VALIDATION_2026-10-07.md for their audit.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/source/original_pipeline"
RECOVERED = ROOT / "data/source/legacy_simulation_archive/230214simulation/raw_data.xlsx"
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"


def parse_date(col: str) -> datetime:
    token = re.search(r"(\d{8}|\d{6})", str(col)).group(1)
    return datetime.strptime(token, "%Y%m%d" if len(token) == 8 else "%Y%m")


def main() -> None:
    pos = pd.read_csv(SRC / "result_pos.csv")
    size = pd.read_csv(SRC / "result_size.csv")
    image_cols = list(size.columns[1:])
    inventory = []
    for col in image_cols:
        dt = parse_date(col)
        inventory.append({"image_column": col, "date": dt.strftime("%Y-%m-%d" if len(re.search(r"(\d{8}|\d{6})", col).group(1)) == 8 else "%Y-%m"),
                          "date_precision": "day" if len(re.search(r"(\d{8}|\d{6})", col).group(1)) == 8 else "month",
                          "year": dt.year, "n_nonmissing_size": int(size[col].replace(-1, pd.NA).notna().sum()),
                          "n_nonmissing_x": int(pos[col + "x"].replace(-1, pd.NA).notna().sum()),
                          "n_nonmissing_y": int(pos[col + "y"].replace(-1, pd.NA).notna().sum())})
    inv = pd.DataFrame(inventory)
    TABLES.mkdir(exist_ok=True); inv.to_csv(TABLES / "original_pipeline_image_inventory.csv", index=False)

    upstream = pd.read_excel(SRC / "mydata_0224.xlsx")
    recovered = pd.read_excel(RECOVERED).rename(columns={"Unnamed: 0": "record_id"})
    keys = ["year", "size", "X", "Y", "growth_rate"]
    a = Counter(map(tuple, upstream[keys].round(8).to_numpy()))
    b = Counter(map(tuple, recovered[keys].round(8).to_numpy()))
    weather = pd.read_excel(SRC / "xiamen.xlsx")
    audit = {
        "upstream_repository": "https://github.com/ydchen0806/ai4FastEvolution",
        "upstream_commit": "171c9f516799b8bc90aa98b9274730ead7ae740e",
        "raw_size_position_rows": int(len(size)),
        "raw_image_dates": [str(x) for x in inv["date"]],
        "raw_image_date_count": int(len(inv)),
        "upstream_final_rows": int(len(upstream)),
        "recovered_environment_growth_rows": int(len(recovered)),
        "upstream_recovered_key_multiset_match": bool(a == b),
        "weather_rows": int(len(weather)),
        "weather_year_min": int(weather.Year.min()),
        "weather_year_max": int(weather.Year.max()),
        "image_pixel_files_found_in_release": False,
        "image_pixel_boundary": "Raw imagery and masks are outside this release snapshot. They were recovered locally on 2026-10-06; see docs/RECOVERY_VALIDATION_2026-10-07.md and data/derived/recovery_20261007/.",
        "model_checkpoint_boundary": "The upstream repository contains AutoGluon predictor artifacts, but no recovered UAV segmentation checkpoint or original training split. Polygon annotations and 79 delivered PNG masks have since been recovered locally.",
    }
    (TABLES / "original_pipeline_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(11, 4.2), constrained_layout=True)
    ax.bar(inv.date, inv.n_nonmissing_size, color="#176B87")
    ax.set(xlabel="Referenced image date", ylabel="Non-missing patch-size rows",
           title="Recovered upstream image-index inventory")
    ax.tick_params(axis="x", rotation=60)
    ax.text(.01, .98, "Counts from archived size matrices; first two dates have month precision only",
            transform=ax.transAxes, va="top", fontsize=8, color="#667085")
    fig.savefig(FIGURES / "fig_original_pipeline_inventory.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / "fig_original_pipeline_inventory.png", dpi=320, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
