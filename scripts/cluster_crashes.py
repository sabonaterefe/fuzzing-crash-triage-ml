#!/usr/bin/env python3
"""
Clusters crash stack traces using three approaches of increasing
sophistication: naive raw-output dedup, frame-signature matching
(Socorro-style), and HDBSCAN over TF-IDF-vectorized stack frames.
"""

import json
from pathlib import Path

import hdbscan
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRASH_DIR = PROJECT_ROOT / "results" / "crashes"
OUT_DIR = PROJECT_ROOT / "results" / "clusters"


def load_crashes():
    return [json.loads(f.read_text()) for f in sorted(CRASH_DIR.glob("*.json"))]


def naive_dedup(records):
    groups = {}
    for r in records:
        groups.setdefault(r["raw_asan_output"], []).append(r["crash_id"])
    return list(groups.values())


def frame_signature(record, top_n=3):
    return "|".join(f["function"] for f in record["frames"][:top_n])



def frame_signature_dedup(records, top_n=3):
    groups = {}
    for r in records:
        groups.setdefault(frame_signature(r, top_n), []).append(r["crash_id"])
    return list(groups.values())


def frame_text(record):
    parts = []
    for f in record["frames"]:
        parts += [f["function"], Path(f["file"]).name, str(f["line"])]
    return " ".join(parts)


def hdbscan_cluster(records, min_cluster_size=2):
    texts = [frame_text(r) for r in records]
    X = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b").fit_transform(texts).toarray()
    labels = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size, metric="euclidean", allow_single_cluster=True
    ).fit_predict(X)

    groups = {}
    for r, label in zip(records, labels):
        groups.setdefault(int(label), []).append(r["crash_id"])
    return groups


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = load_crashes()

    print(f"Loaded {len(records)} crash record(s).\n")

    naive_groups = naive_dedup(records)
    print(f"[naive dedup]          -> {len(naive_groups)} group(s)")
    for g in naive_groups:
        print(f"    {g}")

    sig_groups = frame_signature_dedup(records, top_n=3)
    print(f"\n[frame-signature top3] -> {len(sig_groups)} group(s)")
    for g in sig_groups:
        print(f"    {g}")

    hdb_groups = hdbscan_cluster(records, min_cluster_size=2)
    n_clusters = len([k for k in hdb_groups if k != -1])
    n_noise = len(hdb_groups.get(-1, []))
    print(f"\n[HDBSCAN]               -> {n_clusters} cluster(s), {n_noise} noise point(s)")
    for label, ids in sorted(hdb_groups.items()):
        tag = "noise" if label == -1 else f"cluster {label}"
        print(f"    [{tag}]")
        for i in ids:
            print(f"      {i}")

    summary = {
        "n_crashes": len(records),
        "naive_dedup": {"n_groups": len(naive_groups), "groups": naive_groups},
        "frame_signature": {"n_groups": len(sig_groups), "groups": sig_groups},
        "hdbscan": {
            "n_clusters": n_clusters,
            "n_noise": n_noise,
            "groups": {str(k): v for k, v in hdb_groups.items()},
        },
    }

    (OUT_DIR / "cluster_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nSaved summary to {OUT_DIR / 'cluster_summary.json'}")


if __name__ == "__main__":
    main()
