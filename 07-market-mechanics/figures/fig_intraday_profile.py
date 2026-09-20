"""
Figure 3 - The intraday volume U-shape: when a trading day actually trades.

Free data: 5-minute SPY bars from Yahoo Finance's public chart API
(interval=5m, range=60d, regular session only), cached to data/spy_5m.csv so
the figure is reproducible offline and stable. For every full session the
day's volume is bucketed by time of day; each bucket is expressed as a share
of that day's total volume and then averaged across days. The result is the
classic U-shape: a busy open, a quiet lunch, and a close that is the biggest
liquidity event of the day. The share of the average day's volume that trades
in the first and last 30 minutes is printed and quoted in the text.

No strategy, no thresholds, no tuning - a plain unconditional average of when
volume happens. Sessions with fewer than 70 of the 78 five-minute buckets
(partial or shortened days) are excluded.

Reproducible:
    python fig_intraday_profile.py     # numpy, matplotlib; stdlib urllib/json
"""
import os, json, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spy_5m.csv")


def load_bars():
    """Return list of (date_str, hhmm_str, volume)."""
    if os.path.exists(CACHE):
        rows = []
        with open(CACHE) as f:
            for row in csv.DictReader(f):
                rows.append((row["date"], row["time"], int(row["volume"])))
        return rows
    socket.setdefaulttimeout(30)
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/SPY"
           "?interval=5m&range=60d")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    j = json.loads(urllib.request.urlopen(req).read())
    r = j["chart"]["result"][0]
    off = r["meta"]["gmtoffset"]                     # exchange-local offset, s
    ts = r["timestamp"]
    vol = r["indicators"]["quote"][0]["volume"]
    rows = []
    for t, v in zip(ts, vol):
        if v is None:
            continue
        loc = dt.datetime.utcfromtimestamp(t + off)
        rows.append((loc.strftime("%Y-%m-%d"), loc.strftime("%H:%M"), int(v)))
    with open(CACHE, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "time", "volume"])
        w.writerows(rows)
    return rows


rows = load_bars()

# ---- 78 regular-session buckets 09:30 .. 15:55 ------------------------------
t0 = dt.datetime(2000, 1, 1, 9, 30)
buckets = [(t0 + dt.timedelta(minutes=5 * i)).strftime("%H:%M") for i in range(78)]
b_idx = {b: i for i, b in enumerate(buckets)}

days = {}
for d, hhmm, v in rows:
    if hhmm == "16:00":                 # closing print sometimes stamped 16:00
        hhmm = "15:55"                  # fold it into the last bucket
    if hhmm not in b_idx:
        continue
    days.setdefault(d, np.zeros(78))[b_idx[hhmm]] += v

full = {d: a for d, a in days.items() if (a > 0).sum() >= 70}
shares = np.array([a / a.sum() for a in full.values()])      # day-relative
mean_share = shares.mean(axis=0) * 100                        # % of day per 5 min

first30 = mean_share[:6].sum()
last30 = mean_share[-6:].sum()
trough_i = int(np.argmin(mean_share))
peak_i = int(np.argmax(mean_share))
dates_sorted = sorted(full)

C_BAR, C_ACC, C_INK = "#31567c", "#8a6d3b", "#17120e"

fig, ax = plt.subplots(figsize=(6.9, 4.0))
x = np.arange(78)
ax.bar(x, mean_share, width=0.85, color=C_BAR, alpha=0.8)
ax.axvspan(-0.5, 5.5, color=C_ACC, alpha=0.14)
ax.axvspan(71.5, 77.5, color=C_ACC, alpha=0.14)
ax.text(2.5, mean_share.max() * 0.94, f"first 30 min\n{first30:.1f}% of the day",
        ha="center", fontsize=8.2, color=C_INK)
ax.text(74.5, mean_share.max() * 0.94, f"last 30 min\n{last30:.1f}% of the day",
        ha="center", fontsize=8.2, color=C_INK)
ax.annotate(f"lunchtime trough\n({buckets[trough_i]} bar: "
            f"{mean_share[trough_i]:.2f}%)",
            xy=(trough_i, mean_share[trough_i]),
            xytext=(trough_i - 9, mean_share.max() * 0.52),
            fontsize=8, color=C_INK,
            arrowprops=dict(arrowstyle="->", color=C_INK, lw=0.8))

tick_pos = [b_idx[t] for t in ["09:30", "10:30", "11:30", "12:30",
                               "13:30", "14:30", "15:30"]]
ax.set_xticks(tick_pos)
ax.set_xticklabels(["09:30", "10:30", "11:30", "12:30", "13:30", "14:30",
                    "15:30"], fontsize=8)
ax.set_xlabel("time of day (ET), 5-minute buckets")
ax.set_ylabel("share of the day's volume (%)")
ax.set_title("SPY: the average day is a U — busy open, quiet lunch, "
             "and the close as the main event", fontsize=10.2)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"Yahoo 5-minute SPY bars, regular session, {dates_sorted[0]} – "
         f"{dates_sorted[-1]} ({len(full)} full sessions). Each day normalized "
         "to its own total volume, then averaged.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_intraday_profile.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"n_days={len(full)} span={dates_sorted[0]}..{dates_sorted[-1]}")
print(f"first30_pct={first30:.1f} last30_pct={last30:.1f} "
      f"first_plus_last_hour_pct={mean_share[:12].sum() + mean_share[-12:].sum():.1f}")
print(f"peak_bucket={buckets[peak_i]} peak_pct={mean_share[peak_i]:.2f} "
      f"trough_bucket={buckets[trough_i]} trough_pct={mean_share[trough_i]:.2f} "
      f"last_bar_pct={mean_share[-1]:.2f}")
