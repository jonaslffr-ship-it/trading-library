#!/usr/bin/env python3
"""Generate data/data_manifest.csv.

Fingerprints (sha256) of every SHIPPED data file so a cloner can verify integrity,
plus provenance + an aggregate fingerprint of the licensed RAW datasets (which are
NEVER redistributed) so a licensed holder can verify dataset identity.

    python make_manifest.py              # shipped-file hashes + raw provenance
    python make_manifest.py --hash-raw   # + aggregate sha256 over each raw dataset
                                         #   (streams all raw files, ~1-2 min / 2.7 GB)

SPX+VIX public scope: only the SPX-derived artifacts and the FRED VIX/VIX3M series
are listed (NDX/DAX/NQ raw are out of scope and out of the public repo).
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import os

# shipped-in-repo derived/public files -> per-file sha256 (cloner-verifiable)
SHIPPED = {
    "data/processed/feat_SPX.parquet":     ("SPX",   "derived RV/HAR features from licensed 1-min"),
    "data/processed/ohlc_SPX.parquet":     ("SPX",   "derived daily OHLC from licensed 1-min"),
    "data/processed/vmpred_SPX.parquet":   ("SPX",   "log-HAR OOS variance forecast"),
    "data/processed/spx_2024_5min.parquet":("SPX",   "SPX 2024 5-min sample (reality check)"),
    "data/macro/VIXCLS.csv":               ("VIX",   "FRED VIXCLS, public"),
    "data/macro/VXVCLS.csv":               ("VIX3M", "FRED VXVCLS, public"),
}

# licensed raw datasets -> provenance (+ aggregate hash with --hash-raw)
RAW = {
    "SPX_1min": ("data/raw/*.csv",     "MarketTick", "licensed; not redistributed"),
    "VIX_1min": ("data/raw/vix/*.csv", "MarketTick", "licensed; not redistributed"),
}


def sha256_file(path: str, buf: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def date_range(files):
    ds = sorted(os.path.basename(f)[:8] for f in files if os.path.basename(f)[:8].isdigit())
    return (ds[0], ds[-1]) if ds else ("", "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hash-raw", action="store_true",
                    help="aggregate-hash the raw datasets (slow; for licensed holders)")
    args = ap.parse_args()

    rows = []
    for path, (mkt, note) in SHIPPED.items():
        if not os.path.exists(path):
            continue
        rows.append({"entry": path, "kind": "shipped", "market": mkt,
                     "provider": "derived/FRED", "n_files": 1,
                     "bytes": os.path.getsize(path), "period_start": "", "period_end": "",
                     "sha256": sha256_file(path), "note": note})

    for name, (pattern, provider, lic) in RAW.items():
        files = sorted(glob.glob(pattern))
        if not files:
            continue
        p0, p1 = date_range(files)
        agg = "(run --hash-raw)"
        if args.hash_raw:
            h = hashlib.sha256()
            for fp in files:                        # Merkle-style: hash of per-file hashes
                h.update(sha256_file(fp).encode())
            agg = h.hexdigest()
        rows.append({"entry": name, "kind": "raw", "market": name.split("_")[0],
                     "provider": provider, "n_files": len(files),
                     "bytes": sum(os.path.getsize(f) for f in files),
                     "period_start": p0, "period_end": p1, "sha256": agg, "note": lic})

    cols = ["entry", "kind", "market", "provider", "n_files", "bytes",
            "period_start", "period_end", "sha256", "note"]
    os.makedirs("data", exist_ok=True)
    with open("data/data_manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    n_ship = sum(r["kind"] == "shipped" for r in rows)
    n_raw = sum(r["kind"] == "raw" for r in rows)
    print(f"wrote data/data_manifest.csv: {n_ship} shipped + {n_raw} raw entries "
          f"(hash-raw={args.hash_raw})")


if __name__ == "__main__":
    main()
