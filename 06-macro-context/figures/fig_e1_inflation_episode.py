"""
Figure 3 - The 2020-2024 inflation episode as the modern teaching case.

Free data (FRED public CSV, cached to data/):
  CPIAUCSL - headline CPI index, monthly, SA  -> YoY % computed
  CPILFESL - core CPI (ex food & energy)      -> YoY % computed
  DFEDTARU - fed funds target range, upper limit, daily % (the policy response)

Annotated dates are public-record policy events (first hike 2022-03-16, last
hike 2022-07/2023-07 cycle end 2023-07-26, first cut 2024-09-18, all from
federalreserve.gov statements); inflation turning points are computed from the
data and printed, not hand-picked.

Reproducible:
    python fig_e1_inflation_episode.py     # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)

INK, GREEN, CLARET, BLUE, GREY = "#17120e", "#2f6d4f", "#7c1c2c", "#2b4a6f", "#666"


def fred(series):
    path = os.path.join(DATA, series + ".csv")
    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        try:
            socket.setdefaulttimeout(60)
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + series
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req).read()
            if not raw:
                raise ValueError("empty response")
            tmp = path + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, path)
        except Exception as e:
            print(f"SKIPPED (offline / no cache): {os.path.basename(path)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)
    dates, vals = [], []
    with open(path) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            if len(row) < 2 or row[1] in (".", ""):
                continue
            dates.append(dt.datetime.strptime(row[0], "%Y-%m-%d"))
            vals.append(float(row[1]))
    return dates, np.array(vals)


def yoy_calendar(dates, vals):
    """Calendar-based year-over-year: compare each month with the SAME calendar
    month one year earlier, not with the 12th prior *observation*. A gap in the
    series (e.g. the un-published Oct-2025 CPI) otherwise silently shifts the
    comparison base and biases every later YoY (ERRATA / audit K9)."""
    lut = {(d.year, d.month): v for d, v in zip(dates, vals)}
    out_d, out_v = [], []
    for d, v in zip(dates, vals):
        prev = lut.get((d.year - 1, d.month))
        if prev is not None and prev != 0:
            out_d.append(d)
            out_v.append(100.0 * (v / prev - 1.0))
    return np.array(out_v), out_d


h_d, h = fred("CPIAUCSL")
c_d, c = fred("CPILFESL")
t_d, t = fred("DFEDTARU")

h_yoy, h_yd = yoy_calendar(h_d, h)
c_yoy, c_yd = yoy_calendar(c_d, c)

LO, HI = dt.datetime(2019, 1, 1), dt.datetime(2026, 1, 1)
mh = [i for i, d in enumerate(h_yd) if LO <= d < HI]
mc = [i for i, d in enumerate(c_yd) if LO <= d < HI]
mt = [i for i, d in enumerate(t_d) if LO <= d < HI]

fig, ax = plt.subplots(figsize=(7.0, 4.3))
ax.plot([h_yd[i] for i in mh], h_yoy[mh], "-", color=CLARET, lw=1.6,
        label="headline CPI, % YoY")
ax.plot([c_yd[i] for i in mc], c_yoy[mc], "-", color=INK, lw=1.3,
        label="core CPI (ex food & energy), % YoY")
ax2 = ax.twinx()
ax2.plot([t_d[i] for i in mt], t[mt], "-", color=BLUE, lw=1.3,
         label="fed funds target (upper), %")
ax.axhline(2.0, color=GREEN, lw=0.9, ls="--")
ax.annotate("2% goal (PCE basis)", xy=(dt.datetime(2019, 2, 1), 2.12),
            fontsize=7.6, color=GREEN)

# computed turning points (printed below)
ip = mh[int(np.argmax(h_yoy[mh]))]
peak_d, peak_v = h_yd[ip], h_yoy[ip]
ax.annotate(f"headline peak {peak_v:.1f}%\n({peak_d:%b %Y})",
            xy=(peak_d, peak_v), xytext=(dt.datetime(2020, 8, 1), 7.6),
            fontsize=7.8, color=CLARET,
            arrowprops=dict(arrowstyle="->", color=CLARET, lw=0.8))

events = [
    (dt.datetime(2021, 3, 10), "crosses 2%,\ncalled transitory", 0.6),
    (dt.datetime(2022, 3, 16), "first hike\n(Mar 2022)", 3.1),
    (dt.datetime(2023, 7, 26), "last hike, 5.25–5.50%\n(Jul 2023)", 6.3),
    (dt.datetime(2024, 9, 18), "first cut\n(Sep 2024)", 4.4),
]
for d, txt, y in events:
    ax.axvline(d, color="#bbb", lw=0.7, ls=":")
    ax.annotate(txt, xy=(d, y), fontsize=7.0, color=GREY, ha="left",
                xytext=(d + dt.timedelta(days=18), y))

ax.set_ylabel("inflation, % year-over-year", fontsize=8.6)
ax2.set_ylabel("policy rate, %", fontsize=8.6, color=BLUE)
ax2.tick_params(axis="y", labelcolor=BLUE, labelsize=7.8)
ax.tick_params(labelsize=7.8)
ax.set_ylim(-0.5, 10.2); ax2.set_ylim(-0.5, 10.2)
for s in ("top",):
    ax.spines[s].set_visible(False); ax2.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.22)
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, fontsize=7.6, loc="upper right", frameon=False)
ax.set_title("The 2021–23 inflation episode and the policy response that followed it",
             fontsize=10.2)
fig.text(0.5, -0.02,
         "FRED series CPIAUCSL, CPILFESL (YoY computed), DFEDTARU; policy-event dates "
         "from federalreserve.gov statements. Cached to figures/data/.",
         ha="center", fontsize=7.2, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e1_inflation_episode.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# --- printed numbers quoted in the paper -----------------------------------
print(f"headline peak {peak_v:.1f}% in {peak_d:%Y-%m}")
ic = mc[int(np.argmax(c_yoy[mc]))]
print(f"core peak {c_yoy[ic]:.1f}% in {c_yd[ic]:%Y-%m}")
cross = next(h_yd[i] for i in mh if h_yoy[i] > 2.0 and h_yd[i] >= dt.datetime(2021, 1, 1))
print(f"headline first above 2% (2021 onward): {cross:%Y-%m}")
first_hike = next(t_d[i] for i in range(1, len(t)) if t[i] > t[i - 1]
                  and t_d[i] >= dt.datetime(2021, 1, 1))
print(f"first target-range increase (from data): {first_hike:%Y-%m-%d}")
peak_rate_i = mt[int(np.argmax(t[mt]))]
print(f"target upper peak {t[peak_rate_i]:.2f}%, reached {t_d[peak_rate_i]:%Y-%m-%d}")
first_cut = next(t_d[i] for i in range(1, len(t)) if t[i] < t[i - 1]
                 and t_d[i] >= dt.datetime(2023, 8, 1))
print(f"first cut after the peak (from data): {first_cut:%Y-%m-%d}")
lag = (first_hike - cross).days / 30.44
print(f"lag from first >2% print to first hike: {lag:.0f} months")
print(f"latest: headline {h_yoy[-1]:.1f}% / core {c_yoy[-1]:.1f}% ({h_yd[-1]:%Y-%m}); "
      f"target upper {t[-1]:.2f}% ({t_d[-1]:%Y-%m-%d})")
