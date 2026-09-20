"""
Figure 1 - The four master variables in one picture.

Free data: all series from FRED's public CSV endpoint
(https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>), cached to
data/<SERIES>.csv so the figure is reproducible offline and stable.

Panels (recessions shaded from USREC, the NBER indicator):
  A  Real GDP growth, quarterly annualized % (A191RL1Q225SBEA)
  B  CPI inflation, year-over-year % computed from the CPIAUCSL index
  C  Effective federal funds rate, monthly % (FEDFUNDS)
  D  Federal Reserve total assets, USD trillions (WALCL, weekly)

Nothing is estimated or tuned: the figure only *shows* the four series that
the paper calls the master variables, on their own scales, with recessions
marked. Every number quoted in the text is printed below.

Reproducible:
    python fig_e1_master_vars.py     # numpy, matplotlib; stdlib urllib/csv
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
    """Download a FRED series as CSV (cached); return (list of date, np.array)."""
    path = os.path.join(DATA, series + ".csv")
    if not os.path.exists(path):
        socket.setdefaulttimeout(60)
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + series
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with open(path, "wb") as f:
            f.write(urllib.request.urlopen(req).read())
    dates, vals = [], []
    with open(path) as f:
        r = csv.reader(f)
        next(r)                                   # header: observation_date,<ID>
        for row in r:
            if len(row) < 2 or row[1] in (".", ""):
                continue
            dates.append(dt.datetime.strptime(row[0], "%Y-%m-%d"))
            vals.append(float(row[1]))
    return dates, np.array(vals)


def rec_spans(rd, rv):
    """Turn the monthly USREC 0/1 series into a list of (start, end) spans."""
    spans, start = [], None
    for d, v in zip(rd, rv):
        if v == 1 and start is None:
            start = d
        elif v == 0 and start is not None:
            spans.append((start, d)); start = None
    if start is not None:
        spans.append((start, rd[-1]))
    return spans


gdp_d, gdp = fred("A191RL1Q225SBEA")      # real GDP growth, % SAAR, quarterly
cpi_d, cpi = fred("CPIAUCSL")             # CPI index, monthly, SA
ff_d,  ff  = fred("FEDFUNDS")             # effective fed funds rate, monthly %
bs_d,  bs  = fred("WALCL")                # Fed total assets, weekly, $ millions
rec_d, rec = fred("USREC")                # NBER recession indicator, monthly

# CPI year-over-year % from the index (12-month change)
cpi_yoy = 100.0 * (cpi[12:] / cpi[:-12] - 1.0)
cpi_yoy_d = cpi_d[12:]

START = dt.datetime(1970, 1, 1)
spans = [s for s in rec_spans(rec_d, rec) if s[1] >= START]

fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.4), sharex=False)
(axA, axB), (axC, axD) = axes

panels = [
    (axA, "A · Growth: real GDP, % change (annualized)", gdp_d, gdp, GREEN),
    (axB, "B · Inflation: CPI, % change year-over-year", cpi_yoy_d, cpi_yoy, CLARET),
    (axC, "C · Interest rates: federal funds rate, %",   ff_d,  ff,  BLUE),
    (axD, "D · Liquidity: Fed total assets, $ trillion", bs_d,  bs / 1e6, INK),
]
for ax, title, d, v, col in panels:
    lo = START if d[0] < START else d[0]
    m = [i for i, x in enumerate(d) if x >= lo]
    dd = [d[i] for i in m]; vv = v[m]
    for s0, s1 in spans:
        ax.axvspan(max(s0, dd[0]), s1, color="#d9d9d9", alpha=0.55, lw=0)
    ax.plot(dd, vv, "-", color=col, lw=1.0)
    ax.set_title(title, fontsize=8.6, loc="left")
    ax.tick_params(labelsize=7.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.25)

axA.set_ylim(-11, 17)                      # 2020Q2/Q3 off scale; noted + printed
axA.annotate(f"2020 Q2/Q3 off scale\n({gdp.min():.1f}% / {gdp.max():.1f}%)",
             xy=(dt.datetime(2020, 4, 1), -10.4),
             fontsize=6.8, color=GREY, ha="center", va="bottom")
axA.axhline(0, color="#999", lw=0.7)
axB.axhline(0, color="#999", lw=0.7)

fig.suptitle("The four master variables, 1970–2026 (shaded bands: NBER recessions)",
             fontsize=10.4, y=0.995)
fig.text(0.5, -0.015,
         "Sources: real GDP growth, OECD quarterly national accounts (QoQ, annualized); "
         "CPI, U.S. BLS; fed funds rate, Fed H.15; Fed total assets, Fed H.4.1; "
         "recessions, NBER. Panel D starts 2002 (series start). Cached to figures/data/.",
         ha="center", fontsize=7.2, color=GREY)
plt.tight_layout(rect=(0, 0, 1, 0.98))

OUT = os.path.join(HERE, "fig_e1_master_vars.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)

# --- numbers quoted in the paper -------------------------------------------
i22 = int(np.argmax(cpi_yoy))
print(f"GDP span {gdp_d[0]:%Y-%m}..{gdp_d[-1]:%Y-%m} n={len(gdp)} "
      f"min={gdp.min():.1f}% ({gdp_d[int(np.argmin(gdp))]:%Y-%m}) "
      f"max={gdp.max():.1f}% ({gdp_d[int(np.argmax(gdp))]:%Y-%m}) latest={gdp[-1]:.1f}%")
print(f"CPI YoY peak overall {cpi_yoy.max():.1f}% ({cpi_yoy_d[i22]:%Y-%m}); "
      f"latest {cpi_yoy[-1]:.1f}% ({cpi_yoy_d[-1]:%Y-%m})")
m21 = [i for i, d in enumerate(cpi_yoy_d) if d >= dt.datetime(2020, 1, 1)]
i21 = m21[int(np.argmax(cpi_yoy[m21]))]
print(f"CPI YoY 2020s peak {cpi_yoy[i21]:.1f}% ({cpi_yoy_d[i21]:%Y-%m})")
print(f"Fed funds peak {ff.max():.2f}% ({ff_d[int(np.argmax(ff))]:%Y-%m}); "
      f"latest {ff[-1]:.2f}% ({ff_d[-1]:%Y-%m})")
print(f"Fed assets: start {bs_d[0]:%Y-%m} {bs[0]/1e6:.2f}tn; "
      f"peak {bs.max()/1e6:.2f}tn ({bs_d[int(np.argmax(bs))]:%Y-%m}); "
      f"latest {bs[-1]/1e6:.2f}tn ({bs_d[-1]:%Y-%m})")
print(f"recessions shaded since 1970: {len(spans)}")
