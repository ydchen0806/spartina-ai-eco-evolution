#!/usr/bin/env python3
"""Reproducible audit and exploratory reanalysis of the available Spartina data.

The repository contains patch-level records and a recovered environment-growth
simulation archive, but not the UAV masks, source weather downloads, or trained
segmentation model described in the manuscript. This script separates local
recomputable quantities, the recovered derived workbook and external context
data downloaded from NASA POWER and GBIF. It audits the scenario export before
allowing any counterfactual interpretation.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from scipy.stats import spearmanr, kendalltau, kruskal


_DEFAULT_ROOT = Path(__file__).resolve().parents[2]
_RELEASE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(__import__("os").environ.get("SPARTINA_PROJECT_ROOT", _DEFAULT_ROOT))
if not (ROOT / "230117paper/220920_paper/220328元胞自动机/new plaque info1.csv").exists() and (_RELEASE_ROOT / "data/source/new plaque info1.csv").exists():
    ROOT = _RELEASE_ROOT
PATCH_CSV = ROOT / "230117paper/220920_paper/220328元胞自动机/new plaque info1.csv"
if not PATCH_CSV.exists():
    PATCH_CSV = ROOT / "data/source/new plaque info1.csv"
OUT = Path(__import__("os").environ.get("SPARTINA_OUTPUT_ROOT", Path(__file__).resolve().parents[1]))
EXT = OUT / "external_data"
FIG = OUT / "figures/generated_candidates"
LEGACY_DIR = EXT / "legacy_simulation_archive/230214simulation"
if not LEGACY_DIR.exists():
    LEGACY_DIR = ROOT / "data/source/legacy_simulation_archive/230214simulation"
LEGACY_RAW = LEGACY_DIR / "raw_data.xlsx"

COLORS = {"primary": "#176B87", "accent": "#D55E00", "green": "#2A9D8F", "ink": "#1B2631", "muted": "#7B8794"}


def get_session():
    # The analysis environment sometimes exports a dead localhost proxy.
    import requests

    s = requests.Session()
    s.trust_env = False
    s.headers.update({"User-Agent": "spartina-nature-reanalysis/0.1"})
    return s


def download_context(download: bool = True) -> dict:
    EXT.mkdir(parents=True, exist_ok=True)
    meta = {}
    if not download:
        return meta
    session = get_session()
    # NASA POWER is used only as an openly accessible point-level climate
    # context series; it is not the ERA5-Land series claimed in the old draft.
    nasa_path = EXT / "nasa_power_zhangjiang_2014_2021.json"
    nasa_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    nasa_params = {
        "parameters": "T2M,PRECTOTCORR,WS10M,RH2M",
        "community": "AG", "longitude": 117.60, "latitude": 23.95,
        "start": "20140101", "end": "20211231", "format": "JSON",
    }
    if not nasa_path.exists():
        r = session.get(nasa_url, params=nasa_params, timeout=90)
        r.raise_for_status()
        nasa_path.write_text(r.text)
    meta["nasa_power"] = {"url": nasa_url, "params": nasa_params, "path": str(nasa_path.relative_to(ROOT))}

    # GBIF's accepted name is Sporobolus alterniflorus; the API resolves the
    # historical name Spartina alterniflora to the same taxon.
    gbif_url = "https://api.gbif.org/v1/occurrence/search"
    gbif_params = {"scientificName": "Spartina alterniflora", "country": "CN",
                   "has_coordinate": "true", "limit": 300}
    gbif_path = EXT / "gbif_spartina_china_occurrences.json"
    if not gbif_path.exists():
        r = session.get(gbif_url, params=gbif_params, timeout=90)
        r.raise_for_status()
        gbif_path.write_text(r.text)
    meta["gbif"] = {"url": gbif_url, "params": gbif_params, "path": str(gbif_path.relative_to(ROOT))}
    (EXT / "download_manifest.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def load_patch_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_csv(PATCH_CSV)
    d = d.rename(columns={"father_pos,y": "father_pos_y"})
    d["year"] = d["date"].astype(int)
    d["offspring_parent_ratio"] = d["size"] / d["father_S"]
    d["log10_offspring_parent_ratio"] = np.log10(d["offspring_parent_ratio"])
    d["new_patch_area_proxy"] = d["size"]
    # 2020 and 2021 have a single repeated parent size.  Those rows remain in
    # the raw audit, but are excluded from parent-normalized trend estimates.
    d["parent_size_structurally_informative"] = ~d.groupby("year")["father_S"].transform("nunique").eq(1)
    d["distance_informative"] = ~d.groupby("year")["distance"].transform("nunique").eq(1)
    years = sorted(d.year.unique())
    rows = []
    for y in years:
        g = d[d.year == y]
        gi = g[g.parent_size_structurally_informative]
        gd = g[g.distance_informative]
        rows.append({
            "year": y, "n_new_patches": len(g),
            "median_new_patch_area_proxy": g.new_patch_area_proxy.median(),
            "q25_new_patch_area_proxy": g.new_patch_area_proxy.quantile(.25),
            "q75_new_patch_area_proxy": g.new_patch_area_proxy.quantile(.75),
            "median_parent_size": g.father_S.median(),
            "n_parent_ratio": len(gi),
            "median_log10_offspring_parent_ratio": gi.log10_offspring_parent_ratio.median() if len(gi) else np.nan,
            "q25_log10_offspring_parent_ratio": gi.log10_offspring_parent_ratio.quantile(.25) if len(gi) else np.nan,
            "q75_log10_offspring_parent_ratio": gi.log10_offspring_parent_ratio.quantile(.75) if len(gi) else np.nan,
            "n_distance": len(gd),
            "median_parent_distance_proxy": gd.distance.median() if len(gd) else np.nan,
            "q25_parent_distance_proxy": gd.distance.quantile(.25) if len(gd) else np.nan,
            "q75_parent_distance_proxy": gd.distance.quantile(.75) if len(gd) else np.nan,
            "parent_size_unique": g.father_S.nunique(), "distance_unique": g.distance.nunique(),
        })
    return d, pd.DataFrame(rows)


def parse_nasa() -> pd.DataFrame:
    p = EXT / "nasa_power_zhangjiang_2014_2021.json"
    if not p.exists():
        return pd.DataFrame()
    obj = json.loads(p.read_text())
    vals = obj["properties"]["parameter"]
    dates = sorted(set().union(*(v.keys() for v in vals.values())))
    x = pd.DataFrame({"date": pd.to_datetime(dates), **{k: [vals[k].get(d, np.nan) for d in dates] for k in vals}})
    x["year"] = x.date.dt.year
    x["month"] = x.date.dt.month
    # July is the image month specified in the supplementary draft; annual
    # means are retained to make the choice auditable.
    out = []
    for (y, m), g in x.groupby(["year", "month"]):
        out.append({"year": y, "month": m, **{c: g[c].mean() for c in vals}})
    return pd.DataFrame(out)


def parse_gbif() -> pd.DataFrame:
    p = EXT / "gbif_spartina_china_occurrences.json"
    if not p.exists():
        return pd.DataFrame()
    obj = json.loads(p.read_text())
    rows = []
    for r in obj.get("results", []):
        rows.append({"gbif_key": r.get("key"), "scientific_name": r.get("scientificName"),
                     "year": r.get("year"), "lon": r.get("decimalLongitude"),
                     "lat": r.get("decimalLatitude"), "dataset": r.get("datasetName"),
                     "basis_of_record": r.get("basisOfRecord")})
    return pd.DataFrame(rows)


def load_legacy_raw() -> tuple[pd.DataFrame, dict]:
    """Load the newly recovered 854-row simulation archive and audit scenarios."""
    if not LEGACY_RAW.exists():
        return pd.DataFrame(), {}
    raw = pd.read_excel(LEGACY_RAW)
    raw = raw.rename(columns={"Unnamed: 0": "record_id"})
    scenarios = []
    for p in sorted(LEGACY_DIR.glob("*_simulation.xlsx")):
        d = pd.read_excel(p)
        scenarios.append({
            "scenario": p.stem.replace("_simulation", ""),
            "path": str(p.relative_to(ROOT)),
            "n_rows": len(d),
            "mean_growth_rate_pred": float(d["growth_rate_pred"].mean()),
            "sd_growth_rate_pred": float(d["growth_rate_pred"].std()),
            "mean_growth_rate_simulation": float(d["growth_rate_simulation"].mean()),
            "sd_growth_rate_simulation": float(d["growth_rate_simulation"].std()),
            "pca1_simulation_mean": float(d["pca1_simulation"].mean()),
            "pca2_simulation_mean": float(d["pca2_simulation"].mean()),
            "pca3_simulation_mean": float(d["pca3_simulation"].mean()),
            "pca4_simulation_mean": float(d["pca4_simulation"].mean()),
            "growth_pred_identical_to_raw_archive": bool(np.allclose(d["growth_rate_pred"], raw["growth_rate_simulation"])),
            "growth_output_identical_to_raw_archive": bool(np.allclose(d["growth_rate_simulation"], raw["growth_rate_simulation"])),
        })
    raw["simulation_error"] = raw["growth_rate_simulation"] - raw["growth_rate"]
    raw_summary = raw.groupby("year").agg(
        n=("growth_rate", "size"),
        observed_mean=("growth_rate", "mean"), observed_median=("growth_rate", "median"), observed_sd=("growth_rate", "std"),
        simulated_mean=("growth_rate_simulation", "mean"), simulated_median=("growth_rate_simulation", "median"),
        simulated_sd=("growth_rate_simulation", "std"), error_mean=("simulation_error", "mean"),
        error_rmse=("simulation_error", lambda x: float(np.sqrt(np.mean(np.square(x)))))
    ).reset_index()
    scenarios_df = pd.DataFrame(scenarios)
    r = raw[["growth_rate", "growth_rate_simulation"]].corr().iloc[0, 1]
    audit = {
        "n_rows": int(len(raw)), "years": [int(x) for x in sorted(raw.year.unique())],
        "observed_simulated_rmse": float(np.sqrt(np.mean(raw.simulation_error ** 2))),
        "observed_simulated_mae": float(np.mean(np.abs(raw.simulation_error))),
        "observed_simulated_pearson_r": float(r), "observed_simulated_r2_as_r_squared": float(r * r),
        "scenario_simulation_column_identical": bool(len(scenarios_df) and scenarios_df.growth_output_identical_to_raw_archive.all()),
        "scenario_pred_means": scenarios_df[["scenario", "mean_growth_rate_pred"]].to_dict(orient="records") if len(scenarios_df) else [],
        "scenario_warning": "All seven scenario workbooks contain the same growth_rate_simulation vector despite different pca*_simulation inputs. The separate growth_rate_pred column varies by scenario and is the candidate counterfactual output, but its provenance and export code must be recovered before causal interpretation.",
    }
    return raw, {"summary": raw_summary, "scenarios": scenarios_df, "audit": audit}


def trend_stats(summary: pd.DataFrame, metric: str, years: np.ndarray | None = None) -> dict:
    x = summary.dropna(subset=[metric]).copy()
    if years is not None:
        x = x[x.year.isin(years)]
    if len(x) < 4:
        return {"n_years": len(x), "spearman_rho": np.nan, "spearman_p": np.nan,
                "kendall_tau": np.nan, "kendall_p": np.nan}
    s = spearmanr(x.year, x[metric])
    k = kendalltau(x.year, x[metric])
    return {"n_years": len(x), "spearman_rho": float(s.statistic), "spearman_p": float(s.pvalue),
            "kendall_tau": float(k.statistic), "kendall_p": float(k.pvalue)}


def exploratory_climate_associations(summary: pd.DataFrame, climate: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive rank associations; n is years, not independent patches."""
    if climate.empty:
        return pd.DataFrame()
    x = climate[climate.month == 7].merge(summary, on="year", how="inner")
    outcomes = ["median_log10_offspring_parent_ratio", "n_new_patches", "median_new_patch_area_proxy"]
    predictors = ["T2M", "PRECTOTCORR", "WS10M", "RH2M"]
    rows = []
    for pred in predictors:
        for out in outcomes:
            z = x[[pred, out]].dropna()
            if len(z) < 4:
                continue
            rho, p = spearmanr(z[pred], z[out])
            rows.append({"predictor": pred, "outcome": out, "n_years": len(z),
                         "spearman_rho": float(rho), "nominal_p": float(p),
                         "interpretation": "exploratory; annual time points are not independent experimental replicates"})
    return pd.DataFrame(rows)


def make_figures(d: pd.DataFrame, summary: pd.DataFrame, climate: pd.DataFrame, gbif: pd.DataFrame):
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.linewidth": .7, "figure.dpi": 140})
    years = summary.year.to_numpy()
    valid = summary[summary.n_parent_ratio > 0]
    fig, ax = plt.subplots(2, 2, figsize=(11.2, 7.2), constrained_layout=True)
    # A: detection counts and patch-size proxy
    a = ax[0, 0]
    a.bar(years, summary.n_new_patches, color=COLORS["primary"], alpha=.9, width=.7, label="New patch records")
    a2 = a.twinx(); a2.plot(years, summary.median_new_patch_area_proxy, color=COLORS["accent"], marker="o", lw=2, label="Median area proxy")
    a.set(xlabel="Observation year", ylabel="Number of records", title="A  Patch records and area proxy")
    a2.set_ylabel("Median segmented area (pixels)", color=COLORS["accent"])
    a.set_xticks(years); a.tick_params(axis="x", rotation=45); a.grid(axis="y", alpha=.2)
    a.text(.01, .96, "Counts are detection records; they are not population size", transform=a.transAxes, fontsize=7, color=COLORS["muted"], va="top")
    # B: parent-normalized ratio, with structurally invalid years separated
    b = ax[0, 1]
    order = years
    data = [d.loc[(d.year == y) & d.parent_size_structurally_informative, "log10_offspring_parent_ratio"].dropna() for y in order]
    bp = b.boxplot(data, positions=order, widths=.55, patch_artist=True, showfliers=False,
                   medianprops={"color": COLORS["ink"], "lw": 1.4})
    for box in bp["boxes"]: box.set(facecolor="#A8DADC", edgecolor=COLORS["primary"], alpha=.85)
    b.axvspan(2019.5, 2021.5, color="#F4A261", alpha=.16)
    b.text(2020.5, b.get_ylim()[1], "2020–21 excluded:\nrepeated parent size", ha="center", va="top", fontsize=7, color="#9C4A00")
    b.set(xlabel="Observation year", ylabel="log10(new patch area / parent area)", title="B  Parent-normalized emergence signal")
    b.set_xticks(years); b.tick_params(axis="x", rotation=45); b.grid(axis="y", alpha=.2)
    # C: distance proxy; avoid falsely interpreting 2021 constant values
    c = ax[1, 0]
    c.errorbar(valid.year, valid.median_parent_distance_proxy,
                yerr=[valid.median_parent_distance_proxy-valid.q25_parent_distance_proxy,
                      valid.q75_parent_distance_proxy-valid.median_parent_distance_proxy],
                fmt="o-", color=COLORS["green"], lw=2, capsize=3)
    flagged = summary[summary.n_distance == 0]
    if len(flagged): c.scatter(flagged.year, [d.loc[d.year == y, "distance"].median() for y in flagged.year], marker="x", color="#9C4A00", label="No within-year variation")
    c.set(xlabel="Observation year", ylabel="Parent-distance proxy (pixels)", title="C  Spatial separation of records")
    c.set_xticks(years); c.tick_params(axis="x", rotation=45); c.grid(axis="y", alpha=.2)
    c.legend(frameon=False, fontsize=7, loc="upper left")
    # D: climate context and annual patch metrics, standardized per series
    e = ax[1, 1]
    if len(climate):
        j = climate[climate.month == 7].merge(summary, on="year", how="left")
        for col, lab, color in [("T2M", "July T2M", COLORS["accent"]), ("PRECTOTCORR", "July precipitation", COLORS["primary"]), ("WS10M", "July wind", COLORS["green"])]:
            z = (j[col] - j[col].mean()) / j[col].std(ddof=0)
            e.plot(j.year, z, marker="o", lw=1.8, label=lab, color=color)
        e.plot(j.year, (j.median_log10_offspring_parent_ratio - j.median_log10_offspring_parent_ratio.mean()) / j.median_log10_offspring_parent_ratio.std(ddof=0), marker="s", lw=1.8, label="Patch ratio (z)", color=COLORS["ink"])
        e.axhline(0, color="#999", lw=.7); e.set_xticks(years); e.tick_params(axis="x", rotation=45)
        e.set(xlabel="Year", ylabel="Standardized value", title="D  Climate context (July) and patch signal")
        e.text(.01, .02, "NASA POWER point series; exploratory alignment, n=8 years", transform=e.transAxes, fontsize=7, color=COLORS["muted"])
        e.legend(frameon=False, fontsize=7, ncol=2, loc="best")
    else:
        e.text(.5, .5, "External climate download unavailable", ha="center", va="center")
        e.set_axis_off()
    fig.suptitle("Spartina alterniflora patch-record audit and exploratory reanalysis", fontsize=14, fontweight="bold", color=COLORS["ink"])
    fig.savefig(FIG / "fig_patch_dynamics_audit.png", dpi=320, bbox_inches="tight")
    fig.savefig(FIG / "fig_patch_dynamics_audit.pdf", bbox_inches="tight")
    plt.close(fig)

    if len(gbif):
        fig, ax = plt.subplots(figsize=(7.5, 5.3), constrained_layout=True)
        ax.scatter(gbif.lon, gbif.lat, s=42, c=gbif.year.fillna(gbif.year.min()), cmap="viridis", alpha=.85, edgecolor="white", lw=.5)
        ax.scatter([117.60], [23.95], marker="*", s=180, color=COLORS["accent"], edgecolor="white", lw=.8, label="Zhangjiang Port (approx.)")
        ax.set(xlabel="Longitude", ylabel="Latitude", title="GBIF records labelled Spartina alterniflora in China")
        ax.legend(frameon=False, loc="best")
        cb = fig.colorbar(plt.cm.ScalarMappable(norm=Normalize(gbif.year.min(), gbif.year.max()), cmap="viridis"), ax=ax, pad=.02)
        cb.set_label("Observation year")
        ax.grid(alpha=.2)
        fig.savefig(FIG / "fig_gbif_external_context.png", dpi=320, bbox_inches="tight")
        fig.savefig(FIG / "fig_gbif_external_context.pdf", bbox_inches="tight")
        plt.close(fig)


def make_legacy_figure(raw: pd.DataFrame, legacy: dict):
    if raw.empty:
        return
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.linewidth": .7, "figure.dpi": 140})
    s = legacy["summary"]
    fig, ax = plt.subplots(2, 2, figsize=(11.2, 7.2), constrained_layout=True)
    years = s.year.to_numpy()
    # A: annual observed and simulation means; SEM is descriptive only.
    a = ax[0, 0]
    sem_o = raw.groupby("year").growth_rate.sem().reindex(years).to_numpy()
    sem_s = raw.groupby("year").growth_rate_simulation.sem().reindex(years).to_numpy()
    a.errorbar(years - .08, s.observed_mean, yerr=sem_o, fmt="o-", capsize=3, lw=2, color=COLORS["primary"], label="Observed")
    a.errorbar(years + .08, s.simulated_mean, yerr=sem_s, fmt="s--", capsize=3, lw=1.8, color=COLORS["accent"], label="Simulation export")
    a.set(xlabel="Year", ylabel="Growth-rate index", title="A  Recovered 854-row archive")
    a.set_xticks(years); a.tick_params(axis="x", rotation=45); a.grid(axis="y", alpha=.2); a.legend(frameon=False)
    a.text(.01, .03, "Error bars are within-year SEM; rows are spatial records", transform=a.transAxes, fontsize=7, color=COLORS["muted"])
    # B: calibration scatter
    b = ax[0, 1]
    b.scatter(raw.growth_rate, raw.growth_rate_simulation, s=12, alpha=.35, color=COLORS["primary"], edgecolor="none")
    lo = min(raw.growth_rate.min(), raw.growth_rate_simulation.min()); hi = max(raw.growth_rate.max(), raw.growth_rate_simulation.max())
    b.plot([lo, hi], [lo, hi], color=COLORS["ink"], lw=1, ls=":")
    aud = legacy["audit"]
    b.text(.04, .95, f"RMSE = {aud['observed_simulated_rmse']:.3f}\nr = {aud['observed_simulated_pearson_r']:.3f}", transform=b.transAxes, va="top", fontsize=9)
    b.set(xlabel="Observed growth-rate index", ylabel="Simulated growth-rate index", title="B  Model fit audit")
    b.grid(alpha=.2)
    # C: pca rank associations with observed growth.
    c = ax[1, 0]
    pcas = ["pca1", "pca2", "pca3", "pca4"]
    vals = [spearmanr(raw[p], raw.growth_rate).statistic for p in pcas]
    c.bar(pcas, vals, color=["#457B9D", "#1D3557", "#E76F51", "#2A9D8F"])
    c.axhline(0, color=COLORS["ink"], lw=.7); c.set(xlabel="PCA covariate", ylabel="Spearman ρ", title="C  Environmental association screen")
    c.text(.01, .03, "Record-level associations; spatial and temporal dependence retained", transform=c.transAxes, fontsize=7, color=COLORS["muted"])
    c.grid(axis="y", alpha=.2)
    # D: scenario audit: distinct inputs, invariant output.
    q = legacy["scenarios"]
    d = ax[1, 1]
    if len(q):
        d.bar(q.scenario, q.mean_growth_rate_pred, color=COLORS["primary"], alpha=.9, label="growth_rate_pred")
        d.axhline(q.mean_growth_rate_simulation.iloc[0], color=COLORS["accent"], ls="--", lw=2, label="invariant growth_rate_simulation")
        d.text(.5, .9, "Candidate scenario output varies in growth_rate_pred;\nexported growth_rate_simulation is invariant", ha="center", va="center", transform=d.transAxes, color="#9C4A00", fontsize=8)
        d.set(xlabel="Counterfactual workbook", ylabel="Mean growth-rate index", title="D  Scenario export audit")
        d.tick_params(axis="x", rotation=45); d.grid(axis="y", alpha=.2)
        d.legend(frameon=False, fontsize=7, loc="lower left")
    fig.suptitle("Recovered simulation archive: growth model and export audit", fontsize=14, fontweight="bold", color=COLORS["ink"])
    fig.savefig(FIG / "fig_recovered_simulation_audit.png", dpi=320, bbox_inches="tight")
    fig.savefig(FIG / "fig_recovered_simulation_audit.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-download", action="store_true", help="Use only already downloaded context files")
    args = ap.parse_args()
    meta = download_context(not args.no_download)
    d, summary = load_patch_data()
    climate = parse_nasa(); gbif = parse_gbif()
    climate_assoc = exploratory_climate_associations(summary, climate)
    legacy_raw, legacy = load_legacy_raw()
    OUT.joinpath("tables").mkdir(exist_ok=True)
    d.to_csv(OUT / "tables/patch_records_audited.csv", index=False)
    summary.to_csv(OUT / "tables/patch_year_summary.csv", index=False)
    if len(climate): climate.to_csv(OUT / "tables/nasa_power_year_month_summary.csv", index=False)
    if len(climate_assoc): climate_assoc.to_csv(OUT / "tables/exploratory_climate_associations.csv", index=False)
    if len(gbif): gbif.to_csv(OUT / "tables/gbif_spartina_china.csv", index=False)
    if len(legacy_raw):
        legacy_raw.to_csv(OUT / "tables/recovered_raw_growth_environment.csv", index=False)
        legacy["summary"].to_csv(OUT / "tables/recovered_growth_year_summary.csv", index=False)
        legacy["scenarios"].to_csv(OUT / "tables/recovered_scenario_export_audit.csv", index=False)
    stats = {
        "source_patch_csv": str(PATCH_CSV.relative_to(ROOT)),
        "n_patch_records": int(len(d)), "years": [int(x) for x in sorted(d.year.unique())],
        "parent_ratio_trend_2014_2019": trend_stats(summary, "median_log10_offspring_parent_ratio", np.arange(2014, 2020)),
        "new_record_count_trend_2014_2021": trend_stats(summary, "n_new_patches"),
        "distance_trend_2014_2020": trend_stats(summary, "median_parent_distance_proxy", np.arange(2014, 2021)),
        "exploratory_climate_associations": climate_assoc.to_dict(orient="records"),
        "structural_audit": {str(int(y)): {"parent_size_unique": int(summary.loc[summary.year == y, "parent_size_unique"].iloc[0]), "distance_unique": int(summary.loc[summary.year == y, "distance_unique"].iloc[0])} for y in summary.year},
        "gbif_n_china_records": int(len(gbif)), "context_downloads": meta,
        "recovered_raw_archive": legacy["audit"] if legacy else {},
        "interpretation": "The patch CSV supports descriptive record-level trends. It does not by itself identify generations, heritability, or causal adaptation; 2020-2021 parent-size plateaus are flagged and excluded from parent-normalized trend estimates.",
    }
    (OUT / "tables/reanalysis_audit.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    make_figures(d, summary, climate, gbif)
    make_legacy_figure(legacy_raw, legacy)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
