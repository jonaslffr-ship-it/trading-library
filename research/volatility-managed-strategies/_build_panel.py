"""Build the improvement panel ONCE from the exact paper harness, cache to parquet.
Reuses analyze.build_features (raw 1-min -> RV/BV/jump/semivar/RQ/HAR lags) and
ml_models.add_ivar (VIX^2/252), then adds ivslope = log(VIX3M/VIX). No new DoF."""
import numpy as np, pandas as pd
from analyze import build_features
from ml_models import add_ivar

def _fred(name):
    df = pd.read_csv(f"data/macro/{name}.csv", parse_dates=["observation_date"], index_col="observation_date")
    return df[name].astype(float)

feat = add_ivar(build_features())
idx = feat.index
vix, vxv = _fred("VIXCLS"), _fred("VXVCLS")
feat["ivslope"] = np.log((vxv / vix).reindex(idx).ffill(limit=5))
cols = ["rv","rv_d","rv_w","rv_m","bv","jump","rs_p","rs_m","rq","ret","ret_neg","harq_x","ivar","ivslope","close"]
feat[cols].to_parquet("results/_improve_panel.parquet")
print("panel saved:", feat[cols].shape, feat.index.min().date(), "->", feat.index.max().date())
print("null ivslope:", int(feat['ivslope'].isna().sum()), "| null ivar:", int(feat['ivar'].isna().sum()))
