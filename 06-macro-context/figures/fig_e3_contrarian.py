"""
Figure 4 (E3) - The contrarian claim, tested honestly (pre-registered).

Question: does an EXTREME sentiment reading reverse? We sort each series into
deciles and measure the forward 21-trading-day S&P 500 return that follows.

Two series, both pre-registered with a fixed in-sample / out-of-sample split
whose decile cutoffs are frozen on the in-sample half and then applied,
untouched, to the out-of-sample half (no look-ahead):

  Panel A  VIX close (CBOE, 1990-2026) - the single cleanest market-based
           gauge with the longest free history. TOP decile = extreme fear,
           BOTTOM decile = extreme complacency. In-sample <= 2008-12-31.
  Panel B  Three-family composite (2006-2019, as in fig_e3_composite), rebuilt
           with IN-SAMPLE-ONLY standardization so it is honest out of sample.
           BOTTOM decile = extreme pessimism ("fear"), TOP decile = extreme
           optimism ("complacency"). In-sample <= 2013-06-30.

Pre-registration (frozen before the OOS half is read):
  H0: mean forward 21d SPX return is EQUAL in the extreme-fear and
      extreme-complacency deciles.
  H1 (directional, contrarian): fear-decile forward return > complacency-decile
      forward return (fade the crowd).
  Metric: difference of mean forward 21d returns, fear minus complacency.
  Decision: support H1 iff the difference is > 0 IN-SAMPLE and the SIGN HOLDS
      out-of-sample.

Confidence intervals are moving-block bootstraps (block = the return horizon, so
overlap in the 21-day forward returns is respected; naive i.i.d. errors would be
far too tight). We also print an overlap-adjusted effective n per cell so the
minimum-cell discipline (n_eff < 15) can be checked.

Everything is stdlib csv/zipfile + numpy; no pandas.

Reproducible:
    python fig_e3_contrarian.py
"""
import os, io, csv, socket, zipfile, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
COTDIR = os.path.join(DATA, "cot")
os.makedirs(COTDIR, exist_ok=True)

HORIZON = 21           # forward trading days
SEED = 42
B = 4000               # bootstrap resamples


def fetch(url, path):
    """Cache url -> path. Read into memory first, validate non-empty, then
    write atomically via a .part temp, so a failed/offline fetch never leaves
    a 0-byte or partial cache behind (ERRATA cache-poison). Raises on failure."""
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    socket.setdefaulttimeout(60)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req).read()
    if not raw:
        raise ValueError("empty response")
    tmp = path + ".part"
    with open(tmp, "wb") as f:
        f.write(raw)
    os.replace(tmp, path)


def ensure(url, path):
    """fetch(); on offline failure with no usable cache, SKIP cleanly instead
    of crashing or trusting a poisoned cache."""
    try:
        fetch(url, path)
    except Exception as e:
        if not (os.path.exists(path) and os.path.getsize(path) > 0):
            print(f"SKIPPED (offline / no cache): {os.path.basename(path)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)


# ---------- loaders (cached; read-only reuse of the shared caches) ----------
def load_spx():
    path = os.path.join(DATA, "spx_daily_max.csv")
    dates, close = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            dates.append(row["date"]); close.append(float(row["close"]))
    close = np.array(close)
    pos = {d: i for i, d in enumerate(dates)}
    return dates, close, pos


def load_vix():
    path = os.path.join(DATA, "vix_history.csv")
    ensure("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv", path)
    out = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                d = dt.datetime.strptime(row["DATE"], "%m/%d/%Y").strftime("%Y-%m-%d")
                out[d] = float(row["CLOSE"])
            except (ValueError, KeyError):
                continue
    return out


def load_pc_ma(window=21):
    path = os.path.join(DATA, "equitypc.csv")
    ensure("https://cdn.cboe.com/resources/options/volume_and_call_put_ratios/equitypc.csv", path)
    raw = {}
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) < 5 or "/" not in row[0]:
                continue
            try:
                d = dt.datetime.strptime(row[0].strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
                raw[d] = float(row[4])
            except ValueError:
                continue
    ds = sorted(raw); vals = np.array([raw[d] for d in ds])
    return {ds[i + window - 1]: float(vals[i:i + window].mean())
            for i in range(len(vals) - window + 1)}


def load_cot(code="13874A"):
    rows = {}
    for y in range(1998, 2027):
        zp = os.path.join(COTDIR, f"deacot{y}.zip")
        try:
            fetch(f"https://www.cftc.gov/files/dea/history/deacot{y}.zip", zp)
        except Exception:
            continue
        try:
            z = zipfile.ZipFile(zp)
        except zipfile.BadZipFile:
            continue
        raw = z.read(z.namelist()[0]).decode("latin-1")
        rdr = csv.reader(io.StringIO(raw)); next(rdr)
        for r in rdr:
            if r[3].strip() == code:
                rows[r[2].strip()] = 100.0 * (float(r[8]) - float(r[9])) / float(r[7])
    ds = sorted(rows)
    if not ds:
        print("SKIPPED (offline / no cache): CFTC COT history (data/cot/) unavailable")
        raise SystemExit(0)
    return ds, np.array([rows[d] for d in ds])


# ---------- forward returns ----------
spx_dates, spx_close, spx_pos = load_spx()
N = len(spx_dates)


def fwd_return_at(i):
    """Forward HORIZON-trading-day SPX return from SPX index i."""
    if i is None or i + HORIZON >= N:
        return None
    return spx_close[i + HORIZON] / spx_close[i] - 1.0


def spx_index_on_or_before(day, maxback=6):
    d = dt.datetime.strptime(day, "%Y-%m-%d")
    for k in range(maxback):
        key = (d - dt.timedelta(days=k)).strftime("%Y-%m-%d")
        if key in spx_pos:
            return spx_pos[key]
    return None


# ---------- moving-block bootstrap of cell means and the fear-comp diff ----------
def block_stats(fwd, labels, block, b=B, seed=SEED):
    """fwd, labels time-ordered within one split window. Returns dict of
    {cell: (mean, lo, hi, n)} and (diff, dlo, dhi) for fear-minus-comp."""
    rng = np.random.default_rng(seed)
    n = len(fwd)
    nblk = int(np.ceil(n / block))
    cells = ("fear", "mid", "comp")
    point = {}
    for c in cells:
        m = fwd[labels == c]
        point[c] = (float(m.mean()) if len(m) else np.nan, len(m))
    boot = {c: [] for c in cells}
    dboot = []
    starts_max = n - block
    for _ in range(b):
        starts = rng.integers(0, starts_max + 1, size=nblk)
        idx = np.concatenate([np.arange(s, s + block) for s in starts])[:n]
        fb, lb = fwd[idx], labels[idx]
        mvals = {}
        for c in cells:
            sub = fb[lb == c]
            mvals[c] = sub.mean() if len(sub) else np.nan
            boot[c].append(mvals[c])
        dboot.append(mvals["fear"] - mvals["comp"])
    out = {}
    for c in cells:
        arr = np.array(boot[c], float)
        lo, hi = np.nanpercentile(arr, [2.5, 97.5])
        out[c] = (point[c][0], float(lo), float(hi), point[c][1])
    darr = np.array(dboot, float)
    dpt = point["fear"][0] - point["comp"][0]
    dlo, dhi = np.nanpercentile(darr, [2.5, 97.5])
    return out, (dpt, float(dlo), float(dhi))


# ================= Panel A: VIX (single cleanest series) =================
vix_map = load_vix()
# align VIX to SPX trading days that have a full forward window
vA_dates, vA_val, vA_fwd = [], [], []
for d in sorted(vix_map):
    if d in spx_pos:
        fr = fwd_return_at(spx_pos[d])
        if fr is not None:
            vA_dates.append(d); vA_val.append(vix_map[d]); vA_fwd.append(fr)
vA_val = np.array(vA_val); vA_fwd = np.array(vA_fwd)

VIX_SPLIT = "2008-12-31"
is_mask = np.array([d <= VIX_SPLIT for d in vA_dates])
p10, p90 = np.percentile(vA_val[is_mask], [10, 90])   # cutoffs frozen in-sample


def vix_labels(vals):
    lab = np.full(len(vals), "mid", dtype=object)
    lab[vals >= p90] = "fear"     # high VIX = extreme fear
    lab[vals <= p10] = "comp"     # low VIX  = extreme complacency
    return lab


A_is, A_isd = block_stats(vA_fwd[is_mask], vix_labels(vA_val[is_mask]), HORIZON)
A_oos, A_oosd = block_stats(vA_fwd[~is_mask], vix_labels(vA_val[~is_mask]), HORIZON)
A_full_mean = float(vA_fwd.mean())

# ================= Panel B: three-family composite =================
vix_daily = vix_map
pc_ma = load_pc_ma()
cot_dates, cot = load_cot()


def last_on_or_before_map(m, day, maxback=7):
    d = dt.datetime.strptime(day, "%Y-%m-%d")
    for k in range(maxback):
        key = (d - dt.timedelta(days=k)).strftime("%Y-%m-%d")
        if key in m:
            return m[key]
    return None


rows = []
for d, c in zip(cot_dates, cot):
    friday = (dt.datetime.strptime(d, "%Y-%m-%d") + dt.timedelta(days=3)).strftime("%Y-%m-%d")
    v = last_on_or_before_map(vix_daily, friday)
    p = last_on_or_before_map(pc_ma, friday)
    si = spx_index_on_or_before(friday)
    fr = fwd_return_at(si) if si is not None else None
    if v is not None and p is not None and fr is not None:
        rows.append((friday, v, p, c, fr))

cB_dates = [r[0] for r in rows]
V = np.array([r[1] for r in rows]); P = np.array([r[2] for r in rows])
C = np.array([r[3] for r in rows]); cB_fwd = np.array([r[4] for r in rows])

COMP_SPLIT = "2013-06-30"
isB = np.array([d <= COMP_SPLIT for d in cB_dates])


def zfit(x, mask):
    mu, sd = x[mask].mean(), x[mask].std()
    return (x - mu) / sd


# signed so HIGH composite = optimism; standardize on in-sample only
S = (-zfit(V, isB) - zfit(P, isB) + zfit(C, isB)) / 3.0
q10, q90 = np.percentile(S[isB], [10, 90])   # cutoffs frozen in-sample


def comp_labels(s):
    lab = np.full(len(s), "mid", dtype=object)
    lab[s <= q10] = "fear"    # low optimism = extreme pessimism/fear
    lab[s >= q90] = "comp"    # high optimism = extreme complacency
    return lab


BLOCK_W = 5   # 21 trading days ~ 4-5 weekly rows
B_is, B_isd = block_stats(cB_fwd[isB], comp_labels(S[isB]), BLOCK_W)
B_oos, B_oosd = block_stats(cB_fwd[~isB], comp_labels(S[~isB]), BLOCK_W)
B_full_mean = float(cB_fwd.mean())


def neff(n, overlap):
    return n / overlap


# ================= plot =================
fig, (axA, axB) = plt.subplots(1, 2, figsize=(7.4, 4.4))
cells = ["fear", "mid", "comp"]
cell_lab = {"fear": "extreme\nfear", "mid": "middle\n80%", "comp": "extreme\ncomplacency"}
colA = {"fear": "#7c1c2c", "mid": "#8a8a8a", "comp": "#2f6d4f"}
wid = 0.36
xpos = np.arange(3)


def draw(ax, res_is, res_oos, full_mean, title, sub):
    for k, cell in enumerate(cells):
        for j, (res, hatch, alpha, off) in enumerate(
                [(res_is, None, 0.85, -wid / 2), (res_oos, "///", 0.45, wid / 2)]):
            m, lo, hi, n = res[cell]
            if n == 0 or not np.isfinite(m):
                ax.text(xpos[k] + off, 0.05, "n=0", ha="center", va="bottom",
                        fontsize=6.6, color="#7c1c2c", rotation=90)
                continue
            ax.bar(xpos[k] + off, m * 100, wid, color=colA[cell], alpha=alpha,
                   hatch=hatch, edgecolor="#17120e", lw=0.5)
            ax.errorbar(xpos[k] + off, m * 100, yerr=[[(m - lo) * 100], [(hi - m) * 100]],
                        color="#17120e", lw=0.8, capsize=2)
    ax.axhline(full_mean * 100, color="#17120e", lw=0.8, ls=":")
    ax.axhline(0, color="#999", lw=0.6)
    ax.set_xticks(xpos)
    ax.set_xticklabels([cell_lab[c] for c in cells], fontsize=7.6)
    ax.set_title(title, fontsize=9.6)
    ax.set_ylabel("forward 21-day SPX return (%)", fontsize=8.2)
    ax.tick_params(axis="y", labelsize=7.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.22)
    ax.text(0.5, 0.965, sub, transform=ax.transAxes, ha="center", va="top",
            fontsize=7.0, color="#666")


draw(axA, A_is, A_oos, A_full_mean,
     "A · VIX decile, 1990–2026",
     f"solid = in-sample ≤{VIX_SPLIT} · hatched = OOS")
draw(axB, B_is, B_oos, B_full_mean,
     "B · composite decile, 2006–2019",
     f"solid = in-sample ≤{COMP_SPLIT} · hatched = OOS")

fig.suptitle("Does extreme sentiment reverse? Pre-registered decile test, forward 21-day SPX return",
             fontsize=10.4, y=1.02)
fig.text(0.5, -0.03,
         "Dotted line = full-window mean forward return. Error bars = 95% moving-block bootstrap "
         f"(block={HORIZON}d / {BLOCK_W}w, {B} resamples, seed {SEED}), which respects the overlap "
         "in forward returns. Decile cutoffs frozen in-sample.",
         ha="center", fontsize=7.2, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e3_contrarian.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)


def report(tag, res_is, res_oos, isd, oosd, full_mean, n_is, n_oos, overlap):
    print(f"\n=== {tag} ===  full-window mean fwd21 = {full_mean*100:+.2f}%")
    for split, res, dd, n_all in (("IN-SAMPLE", res_is, isd, n_is),
                                  ("OOS", res_oos, oosd, n_oos)):
        print(f" [{split}] n_total={n_all}")
        for cell in cells:
            m, lo, hi, n = res[cell]
            print(f"   {cell:>5}: mean={m*100:+.2f}%  95%CI[{lo*100:+.2f},{hi*100:+.2f}]  "
                  f"n={n}  n_eff={neff(n, overlap):.0f}")
        dpt, dlo, dhi = dd
        sign = "POS" if dpt > 0 else "NEG"
        excl0 = "excludes 0" if (dlo > 0 or dhi < 0) else "includes 0"
        print(f"   fear-minus-comp = {dpt*100:+.2f}%  95%CI[{dlo*100:+.2f},{dhi*100:+.2f}]  "
              f"({sign}, CI {excl0})")


nA_is = int(is_mask.sum()); nA_oos = int((~is_mask).sum())
nB_is = int(isB.sum()); nB_oos = int((~isB).sum())
report("PANEL A  VIX (fear=top decile, comp=bottom decile)",
       A_is, A_oos, A_isd, A_oosd, A_full_mean, nA_is, nA_oos, HORIZON)
print(f"   VIX cutoffs (in-sample): p10={p10:.2f}  p90={p90:.2f}")
report("PANEL B  composite (fear=bottom decile, comp=top decile)",
       B_is, B_oos, B_isd, B_oosd, B_full_mean, nB_is, nB_oos, BLOCK_W)
print(f"   composite cutoffs (in-sample z): q10={q10:+.3f}  q90={q90:+.3f}")

print("\n--- pre-registered decision ---")
print(f"VIX : in-sample diff {A_isd[0]*100:+.2f}%  ->  OOS diff {A_oosd[0]*100:+.2f}%  "
      f"sign holds: {(A_isd[0] > 0) == (A_oosd[0] > 0) and A_isd[0] > 0}")
print(f"COMP: in-sample diff {B_isd[0]*100:+.2f}%  ->  OOS diff {B_oosd[0]*100:+.2f}%  "
      f"sign holds: {(B_isd[0] > 0) == (B_oosd[0] > 0) and B_isd[0] > 0}")
