"""
Figure 5 - Are scheduled FOMC decision days bigger days for the S&P 500?

Free data: daily S&P 500 closes (Yahoo ^GSPC, cached to data/spx_daily.csv by
the quant-track scripts; copied here), 2011-09-19 .. 2026-09-17.

ONE pre-committed comparison, chosen before the data was examined: the mean
ABSOLUTE close-to-close S&P 500 return on *scheduled* FOMC decision days
versus all other trading days in the sample. No threshold search, no window
search, no alternative event sets: one event list, one metric, reported as-is.

Event list: the decision day (statement day, second day of a two-day meeting)
of every scheduled FOMC meeting inside the sample. Dates 2011-2020 are from the
Federal Reserve's historical meeting calendars; 2021-2026 were re-verified on
federalreserve.gov/monetarypolicy/fomccalendars.htm (fetched 2026-09-18). The
March 2020 scheduled meeting was superseded by emergency actions (2020-03-03
and 2020-03-15); unscheduled actions are NOT in the event list - the question
asked is about the published calendar a trader can know in advance.

Reproducible:
    python fig_e1_event_days.py     # numpy, matplotlib; stdlib csv
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "spx_daily.csv")

INK, GREEN, CLARET, BLUE, GREY = "#17120e", "#2f6d4f", "#7c1c2c", "#2b4a6f", "#666"

FOMC = [
    # 2011 (within sample from 2011-09-19)
    "2011-09-21", "2011-11-02", "2011-12-13",
    # 2012
    "2012-01-25", "2012-03-13", "2012-04-25", "2012-06-20",
    "2012-08-01", "2012-09-13", "2012-10-24", "2012-12-12",
    # 2013
    "2013-01-30", "2013-03-20", "2013-05-01", "2013-06-19",
    "2013-07-31", "2013-09-18", "2013-10-30", "2013-12-18",
    # 2014
    "2014-01-29", "2014-03-19", "2014-04-30", "2014-06-18",
    "2014-07-30", "2014-09-17", "2014-10-29", "2014-12-17",
    # 2015
    "2015-01-28", "2015-03-18", "2015-04-29", "2015-06-17",
    "2015-07-29", "2015-09-17", "2015-10-28", "2015-12-16",
    # 2016
    "2016-01-27", "2016-03-16", "2016-04-27", "2016-06-15",
    "2016-07-27", "2016-09-21", "2016-11-02", "2016-12-14",
    # 2017
    "2017-02-01", "2017-03-15", "2017-05-03", "2017-06-14",
    "2017-07-26", "2017-09-20", "2017-11-01", "2017-12-13",
    # 2018
    "2018-01-31", "2018-03-21", "2018-05-02", "2018-06-13",
    "2018-08-01", "2018-09-26", "2018-11-08", "2018-12-19",
    # 2019
    "2019-01-30", "2019-03-20", "2019-05-01", "2019-06-19",
    "2019-07-31", "2019-09-18", "2019-10-30", "2019-12-11",
    # 2020 (scheduled only; March meeting superseded by emergency actions)
    "2020-01-29", "2020-04-29", "2020-06-10", "2020-07-29",
    "2020-09-16", "2020-11-05", "2020-12-16",
    # 2021
    "2021-01-27", "2021-03-17", "2021-04-28", "2021-06-16",
    "2021-07-28", "2021-09-22", "2021-11-03", "2021-12-15",
    # 2022
    "2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15",
    "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14",
    # 2023
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14",
    "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    # 2024
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
    "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
    "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10",
    # 2026 (through data end 2026-09-17)
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29", "2026-09-16",
]

dates, close = [], []
with open(CACHE) as f:
    for row in csv.DictReader(f):
        dates.append(row["date"]); close.append(float(row["close"]))
close = np.array(close)
ret = np.abs(np.diff(close) / close[:-1]) * 100.0     # |return| in %, day t = dates[t]
rdates = dates[1:]

fomc_set = set(FOMC)
is_f = np.array([d in fomc_set for d in rdates])
matched = {d for d in rdates if d in fomc_set}
unmatched = [d for d in FOMC if d not in matched]

a, b = ret[is_f], ret[~is_f]
ratio = a.mean() / b.mean()

fig, ax = plt.subplots(figsize=(6.8, 4.1))
for x, col, lab in [(b, "#999999", f"all other days (n={len(b)})"),
                    (a, CLARET, f"scheduled FOMC decision days (n={len(a)})")]:
    xs = np.sort(x)
    ax.step(xs, np.arange(1, len(xs) + 1) / len(xs), where="post", color=col,
            lw=1.7, label=lab)
ax.axvline(b.mean(), color="#999999", lw=1.0, ls="--")
ax.axvline(a.mean(), color=CLARET, lw=1.0, ls="--")
ax.annotate(f"mean {b.mean():.2f}%", xy=(b.mean(), 0.06), fontsize=7.8,
            color="#777", rotation=90, va="bottom", ha="right")
ax.annotate(f"mean {a.mean():.2f}%", xy=(a.mean(), 0.06), fontsize=7.8,
            color=CLARET, rotation=90, va="bottom", ha="left")
ax.set_xscale("log")
ax.set_xlim(0.008, 15)
ax.set_xticks([0.01, 0.03, 0.1, 0.3, 1, 3, 10])
ax.set_xticklabels(["0.01", "0.03", "0.1", "0.3", "1", "3", "10"])
ax.set_xlabel("absolute daily S&P 500 return, % (log scale)", fontsize=8.8)
ax.set_ylabel("cumulative share of days", fontsize=8.8)
ax.tick_params(labelsize=7.8)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(True, axis="both", alpha=0.2)
ax.legend(fontsize=8.0, loc="upper left", frameon=False)
ax.set_title(f"Scheduled FOMC decision days move the index ~{ratio:.1f}× more "
             "than ordinary days", fontsize=10.0)
fig.text(0.5, -0.02,
         "Yahoo daily ^GSPC closes 2011-09-19 – 2026-09-17; event list = "
         f"{len(a)} scheduled FOMC decision days (federalreserve.gov calendars). "
         "One pre-committed comparison; unscheduled 2020 emergency actions excluded.",
         ha="center", fontsize=7.2, color=GREY)
plt.tight_layout()

OUT = os.path.join(HERE, "fig_e1_event_days.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

print(f"n_fomc={len(a)} n_other={len(b)} unmatched_event_dates={unmatched}")
print(f"mean_abs_fomc={a.mean():.3f}% mean_abs_other={b.mean():.3f}% "
      f"ratio={ratio:.2f}")
print(f"median_abs_fomc={np.median(a):.3f}% median_abs_other={np.median(b):.3f}% "
      f"median_ratio={np.median(a)/np.median(b):.2f}")
print(f"share |r|>1%: fomc {np.mean(a > 1)*100:.0f}% vs other {np.mean(b > 1)*100:.0f}%")
print(f"largest FOMC-day move {a.max():.2f}% on "
      f"{[d for d, f, r in zip(rdates, is_f, ret) if f and r == a.max()]}")
