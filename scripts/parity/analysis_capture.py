"""
Capture every legacy analysis output for one `AggregationResult` (plan Phase 2.5).

Pure legacy functions are called directly. Two values sit inside Tk methods and are replicated here, each with
its source line: the network info bar (`network_tab.py:381-393`) and the centrality report order
(`network_tab.py:1263`, sorted by betweenness, reverse, stable).
"""

from contextlib import contextmanager
from typing import Dict, Iterator, List

import aggregation_tab
import coherence_scores_tab
import network_tab
import numpy as np
import pca_tab
import range_of_influence_tab
import results_insights_tab
from aggregator import aggregation_method_label

from parity.io_utils import scores_grid


def aggregation_fields(result, requested_method: str) -> Dict:
    """Every `AggregationResult` field plus the method label and the requested method."""
    n = result.n
    return {
        "requested_method": requested_method,
        "method": result.method,
        "label": aggregation_method_label(result),
        "n": n,
        "codes": result.codes,
        "policies": result.policies,
        "decision_makers": result.decision_makers,
        "decision_maker_names": result.decision_maker_names,
        "scores": scores_grid(result.scores, n),
        "ties": [
            {
                "row": tie.row,
                "col": tie.col,
                "code_r": tie.code_r,
                "code_c": tie.code_c,
                "tied_labels": tie.tied_labels,
                "chosen": tie.chosen,
            }
            for tie in result.ties
        ],
        "source_scores": scores_grid(result.source_scores, n),
        "ordinal_cells": scores_grid(result.ordinal_cells, n) if result.ordinal_cells else None,
        "median_even_choice": result.median_even_choice,
    }


def bands(result) -> List[List[str]]:
    """`aggregation_tab._score_bucket` per cell, as the rating label of the bucket."""
    n = result.n
    return [
        [aggregation_tab._SCORE_TO_RATING[aggregation_tab._score_bucket(result.scores.get((i, j)))] for j in range(n)]
        for i in range(n)
    ]


def scores_with_colours(result) -> List[Dict]:
    """`compute_scores` rows with `_value_color` (WOI/WII) and `_count_color` (OI/II) as the table uses them."""
    rows = []
    for row in coherence_scores_tab.compute_scores(result):
        rows.append(
            {
                **row,
                "oi_colour": coherence_scores_tab._count_color(row["oi"], result.n),
                "ii_colour": coherence_scores_tab._count_color(row["ii"], result.n),
                "woi_colour": coherence_scores_tab._value_color(row["woi"]),
                "wii_colour": coherence_scores_tab._value_color(row["wii"]),
            }
        )
    return rows


@contextmanager
def _recorded_svd(store: Dict) -> Iterator[None]:
    """Record the singular values of the SVD call made inside `compute_pca`."""
    original = np.linalg.svd

    def wrapper(*args, **kwargs):
        u, s, vt = original(*args, **kwargs)
        store["singular_values"] = s.tolist()
        return u, s, vt

    np.linalg.svd = wrapper
    try:
        yield
    finally:
        np.linalg.svd = original


def pca(result) -> Dict:
    """`compute_pca` output plus the singular values of its SVD."""
    store: Dict = {"singular_values": None}
    with _recorded_svd(store):
        coords, explained, valid = pca_tab.compute_pca(result)
    s = store["singular_values"]
    variance = [value**2 for value in s] if s else []
    total = float(np.sum(np.asarray(variance))) if variance else 0.0
    # Unrounded percentages exactly as `compute_pca` forms them before `round(pct, 1)` (Option A decision record).
    unrounded = (np.asarray(variance) / total * 100).tolist()[:2] if total else None
    return {
        "coords": coords,
        "explained": explained,
        "explained_unrounded": unrounded,
        "valid": valid,
        "singular_values": s,
    }


def network_info(result) -> Dict:
    """Replicates `network_tab.py:381-393` (the info bar inside `_build_info_bar`)."""
    graph = network_tab._build_graph(result)
    n_edges = len(graph["edges"])
    n_nodes = result.n
    isolated = sum(1 for i in range(n_nodes) if not any(k[0] == i or k[1] == i for k in graph["weights"]))
    max_edges = n_nodes * (n_nodes - 1) if n_nodes > 1 else 1
    density = round(n_edges / max_edges, 3)
    stats_txt = f"{n_nodes} nodes  |  {n_edges} directed edges  |  density: {density}" + (
        f"  |  {isolated} isolated" if isolated else ""
    )
    return {"edge_count": n_edges, "isolated": isolated, "density": density, "stats_text": stats_txt}


def analysis_outputs(result) -> Dict:
    """Bands, scores, entropy, PCA, graph, centrality, network info and the full `compute_insights` output."""
    centrality = network_tab.compute_centrality(result)
    return {
        "bands": bands(result),
        "scores": scores_with_colours(result),
        "entropy": range_of_influence_tab.compute_entropy(result),
        "pca": pca(result),
        "graph_edges": network_tab._build_graph(result)["edges"],
        "centrality": centrality,
        "centrality_ranking": [row["code"] for row in sorted(centrality, key=lambda r: r["betweenness"], reverse=True)],
        "network_info": network_info(result),
        "insights": results_insights_tab.compute_insights(result),
    }
