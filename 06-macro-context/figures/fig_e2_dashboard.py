"""
Figure 5 (E2) - A one-page macro dashboard from public data (the Section 5 build).

Eight panels, all FRED + Yahoo, all cached to data/, NBER recessions (USREC)
shaded throughout: growth (INDPRO YoY), inflation (CPI headline + core YoY),
labor (UNRATE), policy (FEDFUNDS + GS10), cycle clock (10y-3m term spread),
financial conditions (NFCI weekly), SPX vs 200-day average (log), SPX drawdown.
Window: 2000 -> present. Latest values printed for every panel.

Reproducible:
    python fig_e2_dashboard.py    # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
START = 2000.0


def fred(series):
    cache = os.path.join(DATA, f"fred_{series}.csv")
    if not os.path.exists(cache):
        socket.setdefaulttimeout(60)
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with open(cache, "wb") as f:
            f.write(urllib.request.urlopen(req).read())
    d, v = [], []
    with open(cache) as f:
        rdr = csv.reader(f)
        next(rdr)
        for row in rdr:
            if len(row) < 2 or row[1] in (".", ""):
                continue
            d.append(row[0]); v.append(float(row[1]))
    return d, np.array(v)


def frac(dates):
    out = []
    for s in dates:
        y, m = int(s[:4]), int(s[5:7])
        day = int(s[8:10]) if len(s) >= 10 else 15
        out.append(y + ((m - 1) + (day - 0.5) / 31.0) / 12.0)
    return np.array(out)


def yoy_pct(d, v):
    dd = {s[:7]: x for s, x in zip(d, v)}
    out_d, out_v = [], []
    for s, x in zip(d, v):
        prev = f"{int(s[:4])-1:04d}-{s[5:7]}"
        if prev in dd:
            out_d.append(s); out_v.append((x / dd[prev] - 1.0) * 100)
    return out_d, np.array(out_v)


ip_d, ip_v = yoy_pct(*fred("INDPRO"))
cpi_d, cpi_v = yoy_pct(*fred("CPIAUCSL"))
cor_d, cor_v = yoy_pct(*fred("CPILFESL"))
un_d, un_v = fred("UNRATE")
ff_d, ff_v = fred("FEDFUNDS")
g10_d, g10_v = fred("GS10")
tb3_d, tb3_v = fred("TB3MS")
nf_d, nf_v = fred("NFCI")
rec_d, rec_v = fred("USREC")

# term spread on common months
g10m = {s[:7]: x for s, x in zip(g10_d, g10_v)}
tb3m = {s[:7]: x for s, x in zip(tb3_d, tb3_v)}
ts_d = sorted(set(g10m) & set(tb3m))
ts_v = np.array([g10m[m] - tb3m[m] for m in ts_d])
ts_d = [m + "-15" for m in ts_d]

sp_dates, sp_close = [], []
with open(os.path.join(DATA, "spx_daily_max.csv")) as f:
    for row in csv.DictReader(f):
        sp_dates.append(row["date"]); sp_close.append(float(row["close"]))
sp_close = np.array(sp_close)
sp_x = frac(sp_dates)
ma200 = np.convolve(sp_close, np.ones(200) / 200, mode="valid")
ma_x = sp_x[199:]
runmax = np.maximum.accumulate(sp_close)
ddown = (sp_close / runmax - 1.0) * 100

# recession spans (monthly USREC = 1)
rec_spans, in_rec, t0 = [], False, None
rx = frac(rec_d)
for t, v in zip(rx, rec_v):
    if v == 1 and not in_rec:
        in_rec, t0 = True, t
    elif v == 0 and in_rec:
        in_rec = False; rec_spans.append((t0, t))
if in_rec:
    rec_spans.append((t0, rx[-1]))

fig, axes = plt.subplots(4, 2, figsize=(10.5, 12.2), sharex=True)
END = max(sp_x[-1], frac([nf_d[-1]])[0]) + 0.1


def panel(ax, title):
    ax.set_title(title, fontsize=9.4, loc="left")
    ax.set_xlim(START, END)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis="y", alpha=0.22)
    for a, b in rec_spans:
        if b >= START:
            ax.axvspan(max(a, START), b, color="#b9b2a7", alpha=0.35, lw=0)


ax = axes[0, 0]; panel(ax, "Growth - industrial production, YoY %")
m = frac(ip_d) >= START
ax.plot(frac(ip_d)[m], ip_v[m], color="#17120e", lw=1.0)
ax.axhline(0, color="#999", lw=0.8)

ax = axes[0, 1]; panel(ax, "Inflation - CPI YoY % (dark) and core CPI YoY % (red)")
m = frac(cpi_d) >= START
ax.plot(frac(cpi_d)[m], cpi_v[m], color="#17120e", lw=1.0)
m = frac(cor_d) >= START
ax.plot(frac(cor_d)[m], cor_v[m], color="#7c1c2c", lw=1.0, alpha=0.9)
ax.axhline(2, color="#999", lw=0.8, ls="--")

ax = axes[1, 0]; panel(ax, "Labor - unemployment rate, %")
m = frac(un_d) >= START
ax.plot(frac(un_d)[m], un_v[m], color="#17120e", lw=1.0)

ax = axes[1, 1]; panel(ax, "Policy - fed funds (dark) and 10y Treasury % (blue)")
m = frac(ff_d) >= START
ax.plot(frac(ff_d)[m], ff_v[m], color="#17120e", lw=1.0)
m = frac(g10_d) >= START
ax.plot(frac(g10_d)[m], g10_v[m], color="#31607e", lw=1.0, alpha=0.9)

ax = axes[2, 0]; panel(ax, "Cycle clock - term spread 10y minus 3m, pp")
m = frac(ts_d) >= START
ax.plot(frac(ts_d)[m], ts_v[m], color="#17120e", lw=1.0)
ax.axhline(0, color="#7c1c2c", lw=0.9, ls="--")

ax = axes[2, 1]; panel(ax, "Financial conditions - Chicago Fed NFCI (0 = average)")
m = frac(nf_d) >= START
ax.plot(frac(nf_d)[m], nf_v[m], color="#17120e", lw=0.8)
ax.axhline(0, color="#999", lw=0.8)

ax = axes[3, 0]; panel(ax, "S&P 500 (log) with 200-day average")
m = sp_x >= START
ax.plot(sp_x[m], sp_close[m], color="#17120e", lw=0.9)
mm = ma_x >= START
ax.plot(ma_x[mm], ma200[mm], color="#b07d2b", lw=1.0, alpha=0.9)
ax.set_yscale("log")

ax = axes[3, 1]; panel(ax, "S&P 500 drawdown from running maximum, %")
ax.fill_between(sp_x[m], ddown[m], 0, color="#7c1c2c", alpha=0.45, lw=0)

fig.suptitle("One-page macro dashboard - all series free (FRED + Yahoo), recessions shaded",
             fontsize=11.5, y=0.995)
fig.text(0.5, 0.003,
         "FRED: INDPRO, CPIAUCSL, CPILFESL, UNRATE, FEDFUNDS, GS10, TB3MS, NFCI, USREC. Yahoo: ^GSPC daily. "
         "Reproduce with fig_e2_dashboard.py; series cached in figures/data/.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout(rect=[0, 0.012, 1, 0.985])
OUT = os.path.join(HERE, "fig_e2_dashboard.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"latest INDPRO YoY {ip_d[-1][:7]}: {ip_v[-1]:+.2f}%")
print(f"latest CPI YoY {cpi_d[-1][:7]}: {cpi_v[-1]:+.2f}%  core {cor_d[-1][:7]}: {cor_v[-1]:+.2f}%")
print(f"latest UNRATE {un_d[-1][:7]}: {un_v[-1]:.1f}%")
print(f"latest FEDFUNDS {ff_d[-1][:7]}: {ff_v[-1]:.2f}%  GS10 {g10_d[-1][:7]}: {g10_v[-1]:.2f}%")
print(f"latest term spread {ts_d[-1][:7]}: {ts_v[-1]:+.2f}pp")
print(f"latest NFCI {nf_d[-1]}: {nf_v[-1]:+.3f}")
print(f"latest SPX {sp_dates[-1]}: {sp_close[-1]:.0f}  vs 200dma {ma200[-1]:.0f} "
      f"({(sp_close[-1]/ma200[-1]-1)*100:+.1f}%)  drawdown {ddown[-1]:+.2f}%")
print(f"recessions shaded since 2000: {sum(1 for a,b in rec_spans if b>=START)}")
