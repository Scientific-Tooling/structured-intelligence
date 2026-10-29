"""Generate a small, explicitly synthetic AnnData input; no statistical analysis."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

SEED = 20261029


def generate(destination: Path):
    destination.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(SEED)
    genes = [f"demo_gene_{i:03d}" for i in range(80)]
    baseline = rng.uniform(1, 12, len(genes))
    blocks, cells = [], []
    for index in range(8):
        condition = "control" if index < 4 else "treated"
        rates = baseline * rng.lognormal(0, 0.25, len(genes))
        if condition == "treated":
            rates[:8] *= 2
        block = rng.poisson(rates, size=(25, len(genes))).astype(np.int32)
        blocks.append(block)
        cells += [{"cell_id": f"synthetic_{index}_{i}", "sample": f"synthetic_donor_{index}",
                   "condition": condition, "cell_type": "DemoCell"} for i in range(25)]
    counts = np.vstack(blocks)
    obs = pd.DataFrame(cells).set_index("cell_id")
    data = ad.AnnData(X=counts.copy(), obs=obs, var=pd.DataFrame(index=genes))
    data.layers["counts"] = counts.copy()
    data.uns["purpose"] = "Synthetic engineering demonstration; not biological data or a scientific benchmark."
    data.uns["seed"] = SEED
    path = destination / "synthetic-counts.h5ad"
    data.write_h5ad(path)
    recovered = ad.read_h5ad(path)
    assert np.array_equal(recovered.layers["counts"], counts)
    assert recovered.obs["sample"].nunique() == 8
    assert all(recovered.obs.groupby("sample", observed=True)["condition"].nunique() == 1)
    obs.to_csv(destination / "cells.tsv", sep="\t")
    receipt = {"purpose": data.uns["purpose"], "seed": SEED, "cells": 200, "genes": 80,
               "synthetic_samples": 8, "samples_per_condition": 4, "cells_per_sample": 25,
               "counts_dtype": str(counts.dtype), "counts_sha256": hashlib.sha256(counts.tobytes()).hexdigest(),
               "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "roundtrip_verified": True,
               "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "packages": {name: metadata.version(name) for name in ("anndata", "numpy", "pandas", "scipy", "h5py")},
               "analysis_executed": False, "expected_scientific_findings": None}
    (destination / "generation.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dataset": str(path.resolve()), **receipt}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New directory; existing datasets are never overwritten.")
    generate(parser.parse_args().output)
