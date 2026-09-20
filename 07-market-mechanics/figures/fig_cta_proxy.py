"""
Figure 4 - A transparent trend-following (CTA) positioning proxy on free data.

Free data: daily S&P 500 (^GSPC, cached data/spx_daily_max.csv) and TLT
(20+yr Treasury ETF, fetched once from Yahoo's public chart API and cached to
data/tlt_daily.csv). ONE pre-committed, standard ensemble - no tuning:

    signal_t = mean( sign(P_t / P_{t-63}  - 1),
                     sign(P_t / P_{t-126} - 1),
                     sign(P_t / P_{t-252} - 1) )        in {-1, -1/3, +1/3, +1}

i.e. the sign of the trailing 3-, 6- and 12-month return - the textbook
time-series-momentum family (Moskowitz, Ooi & Pedersen 2012). The AGGREGATE
sign (long / short) is the positioning proxy; a "flip" is a sign change of the
ensemble. Flip dates of the last 5 years and the current reading are printed.

Reproducible:
    python fig_cta_proxy.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, csv, json, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)


def yahoo_max(symbol, cache):
    path = os.path.join(DATA, cache)
    if os.path.exists(path):
        dates, close = [], []
        with open(path) as f:
            for row in csv.DictReader(f):
                dates.append(row["date"]); close.append(float(row["close"]))
        return dates, np.array(close)
    socket.setdefaulttimeout(30)
    # explicit epoch bounds: range=max silently degrades to monthly bars for old listings
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?period1=0&period2=9999999999&interval=1d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    ts, cl = r["timestamp"], r["indicators"]["quote"][0]["close"]
    dates, close = [], []
    for t, c in zip(ts, cl):
        if c is None:
            continue
        dates.append(dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d"))
        close.append(float(c))
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close"])
        for d, c in zip(dates, close):
            w.writerow([d, f"{c:.4f}"])
    return dates, np.array(close)


def load_cached(cache, start=None):
    dates, close = [], []
    with open(os.path.join(DATA, cache)) as f:
        for row in csv.DictReader(f):
            if start is None or row["date"] >= start:
                dates.append(row["date"]); close.append(float(row["close"]))
    return dates, np.array(close)


LOOKBACKS = (63, 126, 252)


def ensemble(close):
    n = len(close)
    sig = np.full(n, np.nan)
    for i in range(max(LOOKBACKS), n):
        s = [np.sign(close[i] / close[i - lb] - 1.0) for lb in LOOKBACKS]
        sig[i] = np.mean(s)
    return sig


def signs(dates, sig):
    """Daily net sign of the ensemble (0 carries the previous sign)."""
    ds, ss, prev = [], [], 0.0
    for d, s in zip(dates, sig):
        if np.isnan(s):
            continue
        cur = np.sign(s) if s != 0 else prev
        ds.append(d); ss.append(cur); prev = cur
    return ds, np.array(ss)


PERSIST = 10  # trading days a new sign must hold to count as a flip episode


def flips(dates, sig, persist=PERSIST):
    """(raw_crossings, episodes): every sign change vs. changes held >= persist days."""
    ds, ss = signs(dates, sig)
    raw = int(np.sum((ss[1:] != ss[:-1]) & (ss[1:] != 0) & (ss[:-1] != 0)))
    episodes, state = [], 0.0
    for i in range(len(ss)):
        if ss[i] == 0:
            continue
        if state == 0:
            state = ss[i]
        elif ss[i] != state:
            if i + persist <= len(ss) and np.all(ss[i:i + persist] == ss[i]):
                episodes.append((ds[i], "+long" if ss[i] > 0 else "-short"))
                state = ss[i]
    return raw, episodes


spx_d, spx_c = load_cached("spx_daily_max.csv", start="1998-01-01")
tlt_d, tlt_c = yahoo_max("TLT", "tlt_daily.csv")

spx_sig = ensemble(spx_c)
tlt_sig = ensemble(tlt_c)
spx_raw, spx_flips = flips(spx_d, spx_sig)
tlt_raw, tlt_flips = flips(tlt_d, tlt_sig)

# ---- plot ----------------------------------------------------------------
PLOT_FROM = "2004-01-01"
fig, axes = plt.subplots(2, 1, figsize=(7.0, 5.2), sharex=True)
for ax, dts, sig, name, col in ((axes[0], spx_d, spx_sig, "S&P 500 (^GSPC)", "#17120e"),
                                (axes[1], tlt_d, tlt_sig, "TLT (20y+ Treasuries)", "#3b5b78")):
    p0 = np.searchsorted(dts, PLOT_FROM)
    x = [dt.datetime.strptime(d, "%Y-%m-%d") for d in dts[p0:]]
    ax.plot(x, sig[p0:], color=col, lw=0.8, drawstyle="steps-post")
    ax.fill_between(x, 0, sig[p0:], step="post", where=(sig[p0:] > 0),
                    color="#2f6d4f", alpha=0.25, lw=0)
    ax.fill_between(x, 0, sig[p0:], step="post", where=(sig[p0:] < 0),
                    color="#7c1c2c", alpha=0.30, lw=0)
    ax.axhline(0, color="#999", lw=0.7)
    ax.set_ylim(-1.15, 1.15); ax.set_yticks([-1, 0, 1])
    ax.set_ylabel(name, fontsize=8.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.2)
for d, lab in (("2008-01-09", "2008"), ("2009-06-01", "2009"), ("2015-08-25", "2015"),
               ("2018-12-17", "Q4-18"), ("2020-03-03", "Mar-20"), ("2020-06-04", "Jun-20"),
               ("2022-02-11", "2022"), ("2023-02-01", "2023")):
    axes[0].annotate(lab, xy=(dt.datetime.strptime(d, "%Y-%m-%d"), 1.02),
                     fontsize=6.8, color="#666", ha="center")
axes[0].set_title("Trend-ensemble positioning proxy: sign of the 3/6/12-month return",
                  fontsize=10.2)
fig.text(0.5, -0.015,
         f"^GSPC {spx_d[0]}–{spx_d[-1]} (cached), TLT {tlt_d[0]}–{tlt_d[-1]} (Yahoo, cached). "
         "Ensemble = mean of sign(3m), sign(6m), sign(12m) return; plotted from 2004. No tuning.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_cta_proxy.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# ---- printed numbers ------------------------------------------------------
print(f"SPX span {spx_d[0]}..{spx_d[-1]} n={len(spx_c)}; TLT span {tlt_d[0]}..{tlt_d[-1]} n={len(tlt_c)}")
print(f"SPX current reading ({spx_d[-1]}): {spx_sig[-1]:+.2f}")
print(f"TLT current reading ({tlt_d[-1]}): {tlt_sig[-1]:+.2f}")
cut = (dt.datetime.strptime(spx_d[-1], "%Y-%m-%d") - dt.timedelta(days=5 * 365)).strftime("%Y-%m-%d")
print(f"SPX flip EPISODES (sign held >= {PERSIST} trading days) since {cut}:")
for d, lab in spx_flips:
    if d >= cut:
        print(f"  {d}  -> {lab}")
print(f"TLT flip EPISODES since {cut}:")
for d, lab in tlt_flips:
    if d >= cut:
        print(f"  {d}  -> {lab}")
print(f"SPX {spx_d[max(LOOKBACKS)]}..{spx_d[-1]}: raw zero-crossings={spx_raw}, "
      f"persistent episodes={len(spx_flips)}")
print(f"TLT {tlt_d[max(LOOKBACKS)]}..{tlt_d[-1]}: raw zero-crossings={tlt_raw}, "
      f"persistent episodes={len(tlt_flips)}")
frac_long = np.nanmean(spx_sig[np.isfinite(spx_sig)] > 0)
print(f"SPX fraction of days net-long: {100*frac_long:.0f}%")
