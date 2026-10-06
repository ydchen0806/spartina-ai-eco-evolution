#!/usr/bin/env python3
"""Collect pinned external context for the Spartina reanalysis.

The downloads are deliberately kept separate from the local patch archive.
GBIF is used for broad occurrence context and OpenAlex is used to make the
literature search reproducible; neither source is treated as a causal test of
the Zhangjiang invasion record.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd
import requests
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "external_data"
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"
GBIF_API = "https://api.gbif.org/v1"
OPENALEX_API = "https://api.openalex.org/works"
TAXON_NAME = "Sporobolus alterniflorus"


def session() -> requests.Session:
    s = requests.Session()
    s.trust_env = False
    s.headers.update({"User-Agent": "spartina-ai-eco-evolution/0.2"})
    return s


def fetch_gbif(s: requests.Session, download: bool) -> dict:
    EXT.mkdir(exist_ok=True)
    taxon_path = EXT / "gbif_spartina_taxon_match.json"
    facet_path = EXT / "gbif_spartina_global_country_facets.json"
    occ_path = EXT / "gbif_spartina_global_occurrences.json"
    if download or not taxon_path.exists():
        taxon = s.get(f"{GBIF_API}/species/match", params={"name": TAXON_NAME}, timeout=60)
        taxon.raise_for_status(); taxon_path.write_text(taxon.text)
    else:
        taxon = None
    match = json.loads(taxon_path.read_text())
    key = int(match.get("acceptedUsageKey") or match["usageKey"])
    params = {"taxon_key": key, "has_coordinate": "true", "facet": "country",
              "facetMincount": 1, "limit": 0}
    if download or not facet_path.exists():
        r = s.get(f"{GBIF_API}/occurrence/search", params=params, timeout=60)
        r.raise_for_status(); facet_path.write_text(r.text)
    facets = json.loads(facet_path.read_text())
    if download or not occ_path.exists():
        # GBIF reports the complete count in the facet response.  We retain a
        # bounded first page for spatial context rather than presenting a
        # convenience sample as a population census.
        q = {"taxon_key": key, "has_coordinate": "true", "limit": 10, "offset": 0}
        r = s.get(f"{GBIF_API}/occurrence/search", params=q, timeout=60)
        r.raise_for_status(); page = r.json(); rows = page.get("results", [])
        occ_path.write_text(json.dumps({"taxon": match, "count": page.get("count", 0),
                                         "downloaded_first_page": len(rows), "results": rows}, ensure_ascii=False))
    obj = json.loads(occ_path.read_text())
    rows = []
    for r in obj.get("results", []):
        rows.append({"gbif_key": r.get("key"), "country": r.get("country"),
                     "year": r.get("year"), "lon": r.get("decimalLongitude"),
                     "lat": r.get("decimalLatitude"), "basis_of_record": r.get("basisOfRecord"),
                     "dataset": r.get("datasetName"), "occurrence_status": r.get("occurrenceStatus")})
    occ = pd.DataFrame(rows)
    facet_rows = []
    for facet in facets.get("facets", []):
        if facet.get("field") == "COUNTRY":
            facet_rows = [{"country": x.get("name"), "n_records": x.get("count")} for x in facet.get("counts", [])]
    country = pd.DataFrame(facet_rows)
    if len(country):
        TABLES.mkdir(exist_ok=True); country.to_csv(TABLES / "gbif_spartina_global_country_summary.csv", index=False)
    if len(occ):
        occ.to_csv(TABLES / "gbif_spartina_global_occurrences.csv", index=False)
    return {"accepted_taxon_key": key, "reported_occurrence_count": int(obj.get("count", len(occ))),
            "downloaded_first_page": int(len(occ)),
            "country_count": int(len(country)),
            "taxon_match": str(taxon_path.relative_to(ROOT)),
            "facet_file": str(facet_path.relative_to(ROOT)),
            "occurrence_file": str(occ_path.relative_to(ROOT))}


def fetch_openalex(s: requests.Session, download: bool) -> dict:
    EXT.mkdir(exist_ok=True)
    path = EXT / "openalex_literature_search.json"
    queries = ["Spartina alterniflora invasion", "rapid evolution invasive plants",
               "remote sensing biological invasion machine learning"]
    results = []
    if download or not path.exists():
        for query in queries:
            r = s.get(OPENALEX_API, params={"search": query, "per-page": 25,
                                             "select": "id,title,publication_year,doi,cited_by_count,primary_location,authorships"}, timeout=60)
            r.raise_for_status()
            results.append({"query": query, "results": r.json().get("results", [])})
            time.sleep(0.2)
        path.write_text(json.dumps({"queries": results}, ensure_ascii=False))
    else:
        results = json.loads(path.read_text()).get("queries", [])
    rows = []
    for block in results:
        for w in block.get("results", []):
            loc = w.get("primary_location") or {}
            source = loc.get("source") or {}
            rows.append({"query": block.get("query"), "openalex_id": w.get("id"),
                         "title": w.get("title"), "publication_year": w.get("publication_year"),
                         "doi": w.get("doi"), "cited_by_count": w.get("cited_by_count"),
                         "is_open_access": loc.get("is_oa"), "journal": source.get("display_name")})
    lit = pd.DataFrame(rows).drop_duplicates(subset=["doi", "title"])
    TABLES.mkdir(exist_ok=True); lit.to_csv(TABLES / "external_literature_screen.csv", index=False)
    return {"queries": queries, "n_records": int(len(lit)), "file": str(path.relative_to(ROOT))}


def make_context_figure() -> None:
    country_path = TABLES / "gbif_spartina_global_country_summary.csv"
    lit_path = TABLES / "external_literature_screen.csv"
    if not country_path.exists() or not lit_path.exists():
        return
    country = pd.read_csv(country_path).sort_values("n_records", ascending=True)
    lit = pd.read_csv(lit_path).groupby("query").size().sort_values()
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.4), constrained_layout=True)
    ax[0].barh(country.country, country.n_records, color="#176B87")
    ax[0].set_xscale("log"); ax[0].set_xlabel("GBIF records (log scale)")
    ax[0].set_title("A  Global occurrence context")
    ax[0].text(.02, .02, "Accepted name: Sporobolus alterniflorus;\nfacets report 4,584 georeferenced records",
               transform=ax[0].transAxes, fontsize=7, color="#667085")
    ax[1].barh([q[:34] for q in lit.index], lit.values, color="#D55E00")
    ax[1].set_xlabel("OpenAlex works retrieved")
    ax[1].set_title("B  Reproducible literature screen")
    ax[1].text(.02, .02, "Search results support framing and citation discovery;\nthis is not a systematic review.",
               transform=ax[1].transAxes, fontsize=7, color="#667085")
    fig.suptitle("External context for the Spartina eco-evolutionary project", fontsize=13, fontweight="bold")
    fig.savefig(FIGURES / "fig_external_context_synthesis.pdf", bbox_inches="tight")
    fig.savefig(FIGURES / "fig_external_context_synthesis.png", dpi=320, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-download", action="store_true", help="Use pinned response files")
    args = ap.parse_args()
    s = session()
    out = {"gbif": fetch_gbif(s, not args.no_download), "openalex": fetch_openalex(s, not args.no_download),
           "interpretation": "External context and literature screening are not causal validation of the local invasion archive."}
    make_context_figure()
    (TABLES / "external_context_audit.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
