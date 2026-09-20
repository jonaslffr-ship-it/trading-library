"""
Figure 1 (E3) - CFTC Commitments of Traders: net non-commercial positioning
in E-mini S&P 500 futures, 1998-2026.

Free data: the CFTC's legacy futures-only COT history files
(https://www.cftc.gov/files/dea/history/deacotYYYY.zip, one zip per year,
each containing annual.txt), cached to data/cot/. The E-mini S&P 500 contract
is CFTC market code 13874A. Net non-commercial position = non-commercial longs
minus non-commercial shorts, normalized by total open interest so that the
series is comparable across two decades of contract growth. S&P 500 daily
closes from the cached Yahoo series (data/spx_daily_max.csv).

Everything is parsed with the standard library (zipfile + csv); no pandas.

Reproducible:
    python fig_e3_cot.py     # numpy, matplotlib; stdlib urllib/zipfile/csv
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

YEARS = range(1998, 2027)
CODE = "13874A"          # E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE


def fetch(url, path):
    if os.path.exists(path):
        return
    socket.setdefaulttimeout(60)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with open(path, "wb") as f:
        f.write(urllib.request.urlopen(req).read())


def load_cot(code):
    """Weekly (as-of Tuesday) records for one CFTC contract-market code."""
    rows = {}
    for y in YEARS:
        zp = os.path.join(COTDIR, f"deacot{y}.zip")
        try:
            fetch(f"https://www.cftc.gov/files/dea/history/deacot{y}.zip", zp)
        except Exception:
            continue
        z = zipfile.ZipFile(zp)
        raw = z.read(z.namelist()[0]).decode("latin-1")
        rdr = csv.reader(io.StringIO(raw))
        header = next(rdr)
        for r in rdr:
            if r[3].strip() != code:
                continue
            d = r[2].strip()                       # As of Date, YYYY-MM-DD
            oi = float(r[7]); lo = float(r[8]); sh = float(r[9])
            rows[d] = (oi, lo, sh)                 # dedupe on date
    dates = sorted(rows)
    oi = np.array([rows[d][0] for d in dates])
    net = np.array([rows[d][1] - rows[d][2] for d in dates])
    return dates, net, oi


def load_spx():
    path = os.path.join(DATA, "spx_daily_max.csv")
    dates, close = [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            dates.append(row["date"]); close.append(float(row["close"]))
    return dates, np.array(close)


cot_dates, net, oi = load_cot(CODE)
pct_oi = 100.0 * net / oi
spx_dates, spx = load_spx()
i0 = next(i for i, d in enumerate(spx_dates) if d >= cot_dates[0])
sd, sc = spx_dates[i0:], spx[i0:]

x_cot = [dt.datetime.strptime(d, "%Y-%m-%d") for d in cot_dates]
x_spx = [dt.datetime.strptime(d, "%Y-%m-%d") for d in sd]

# current percentile of the latest reading within the full history
cur = pct_oi[-1]
cur_pctile = 100.0 * (pct_oi < cur).mean()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 5.4), sharex=True,
                               gridspec_kw={"height_ratios": [1.0, 1.3]})
ax1.plot(x_spx, sc, "-", color="#17120e", lw=1.0)
ax1.set_yscale("log")
ax1.set_ylabel("S&P 500 (log)")
ax1.set_yticks([1000, 2000, 4000, 8000])
ax1.set_yticklabels(["1,000", "2,000", "4,000", "8,000"])
ax1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())

ax2.axhline(0, color="#999", lw=0.8)
ax2.fill_between(x_cot, pct_oi, 0, where=(pct_oi >= 0), color="#2f6d4f", alpha=0.55, lw=0)
ax2.fill_between(x_cot, pct_oi, 0, where=(pct_oi < 0), color="#7c1c2c", alpha=0.55, lw=0)
ax2.plot(x_cot, pct_oi, "-", color="#17120e", lw=0.7)
ax2.set_ylabel("net non-commercial, % of OI")
ax2.plot(x_cot[-1], cur, "o", color="#17120e", ms=4)
ax2.annotate(f"latest {cur:+.1f}% ({cur_pctile:.0f}th pctile)",
             xy=(x_cot[-1], cur), xytext=(x_cot[-int(len(x_cot)*0.33)], min(pct_oi) * 0.9),
             fontsize=8.5, color="#17120e",
             arrowprops=dict(arrowstyle="->", color="#666", lw=0.8))

imax, imin = int(np.argmax(pct_oi)), int(np.argmin(pct_oi))
ax2.annotate(f"{pct_oi[imax]:+.1f}%  {cot_dates[imax][:7]}", xy=(x_cot[imax], pct_oi[imax]),
             xytext=(0, 4), textcoords="offset points", fontsize=7.5, color="#2f6d4f", ha="center")
ax2.annotate(f"{pct_oi[imin]:+.1f}%  {cot_dates[imin][:7]}", xy=(x_cot[imin], pct_oi[imin]),
             xytext=(18, -2), textcoords="offset points", fontsize=7.5, color="#7c1c2c", ha="left")
ax2.set_ylim(min(pct_oi) * 1.12, max(pct_oi) * 1.18)

for ax in (ax1, ax2):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)
ax1.set_title("Large speculators in E-mini S&P 500 futures: two decades of net positioning",
              fontsize=10.2)
fig.text(0.5, -0.015,
         f"CFTC legacy COT (futures only), E-mini S&P 500 (code 13874A), weekly as-of-Tuesday, "
         f"{cot_dates[0]}–{cot_dates[-1]}, {len(cot_dates)} reports. S&P 500: Yahoo daily.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e3_cot.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={cot_dates[0]}..{cot_dates[-1]} n_weeks={len(cot_dates)}")
print(f"latest_net_pct_oi={cur:+.2f} latest_pctile={cur_pctile:.1f}")
print(f"max_net={pct_oi[imax]:+.2f}% on {cot_dates[imax]}  min_net={pct_oi[imin]:+.2f}% on {cot_dates[imin]}")
print(f"mean={pct_oi.mean():+.2f}% sd={pct_oi.std():.2f}% frac_weeks_net_short={(pct_oi<0).mean():.2f}")
print(f"latest_net_contracts={net[-1]:+.0f} latest_oi={oi[-1]:.0f}")
