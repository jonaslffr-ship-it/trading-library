"""
Figure 3 (E2) - The original Taylor (1993) rule vs. the actual federal funds rate.

Rule, with Taylor's own coefficients, stated in advance and not tuned:
    i = r* + pi + 0.5 (pi - pi*) + 0.5 y
with r* = 2, pi* = 2, pi = core PCE inflation YoY (FRED PCEPILFE), and the
output gap y proxied via Okun's law from the unemployment gap:
    y ~ 2 x (NROU - UNRATE)     (Okun coefficient 2)
so the unemployment gap enters with coefficient 1.0. NROU is the CBO natural
rate (quarterly, forward-filled to months). Compared with FEDFUNDS (monthly
average). Everything is final-vintage data - the real-time caveat (Orphanides
1998) applies and is discussed in the text.

Data: FRED CSV endpoint, cached to data/.

Reproducible:
    python fig_e2_taylor.py    # numpy, matplotlib; stdlib urllib/csv
"""
import os, csv, socket, urllib.request
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)


def fred(series):
    cache = os.path.join(DATA, f"fred_{series}.csv")
    if not (os.path.exists(cache) and os.path.getsize(cache) > 0):
        try:
            socket.setdefaulttimeout(60)
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raw = urllib.request.urlopen(req).read()
            if not raw:
                raise ValueError("empty response")
            tmp = cache + ".part"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, cache)
        except Exception as e:
            print(f"SKIPPED (offline / no cache): {os.path.basename(cache)} - "
                  f"{type(e).__name__}: {e}")
            raise SystemExit(0)
    ym, val = [], []
    with open(cache) as f:
        rdr = csv.reader(f)
        next(rdr)
        for row in rdr:
            if len(row) < 2 or row[1] in (".", ""):
                continue
            ym.append(row[0][:7]); val.append(float(row[1]))
    return ym, np.array(val)


pce_ym, pce = fred("PCEPILFE")     # core PCE price index, monthly
un_ym, un = fred("UNRATE")         # unemployment rate, monthly
nr_ym, nr = fred("NROU")           # CBO natural rate, quarterly
ff_ym, ff = fred("FEDFUNDS")       # effective fed funds, monthly avg

pce_d = {m: v for m, v in zip(pce_ym, pce)}
pi = {}
for m, v in zip(pce_ym, pce):
    prev = f"{int(m[:4])-1:04d}-{m[5:7]}"
    if prev in pce_d:
        pi[m] = (v / pce_d[prev] - 1.0) * 100

# quarterly NROU -> monthly forward fill within the quarter
nrou = {}
for m, v in zip(nr_ym, nr):
    y, q0 = int(m[:4]), int(m[5:7])
    for k in range(3):
        t = y * 12 + (q0 - 1) + k
        nrou[f"{t//12:04d}-{t%12+1:02d}"] = v

un_d = {m: v for m, v in zip(un_ym, un)}
ff_d = {m: v for m, v in zip(ff_ym, ff)}

months = sorted(set(pi) & set(nrou) & set(un_d) & set(ff_d))
rule = np.array([2.0 + pi[m] + 0.5 * (pi[m] - 2.0) + 1.0 * (nrou[m] - un_d[m])
                 for m in months])
actual = np.array([ff_d[m] for m in months])
gap = rule - actual
x = np.array([int(m[:4]) + (int(m[5:7]) - 0.5) / 12 for m in months])

fig, ax = plt.subplots(figsize=(9.2, 4.3))
ax.plot(x, actual, color="#17120e", lw=1.3, label="effective federal funds rate")
ax.plot(x, rule, color="#7c1c2c", lw=1.1, alpha=0.9,
        label="Taylor (1993) rule, core PCE + Okun unemployment gap")
ax.fill_between(x, actual, rule, color="#7c1c2c", alpha=0.10, lw=0)
ax.axhline(0, color="#999", lw=0.8)
ax.set_ylabel("percent, annualized")
ax.set_title("A fixed-coefficient Taylor rule tracks the broad shape of policy - and the gaps are the story",
             fontsize=10.2)
ax.legend(frameon=False, fontsize=8.6, loc="upper right")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.03,
         f"FRED PCEPILFE, UNRATE, NROU, FEDFUNDS, {months[0]}..{months[-1]}. "
         "i = 2 + pi + 0.5(pi-2) + 1.0(NROU-UNRATE); final-vintage data (Orphanides caveat applies).",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_e2_taylor.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"span={months[0]}..{months[-1]} n={len(months)}")
print(f"latest {months[-1]}: rule={rule[-1]:.2f}% actual={actual[-1]:.2f}% gap={gap[-1]:+.2f}pp")
print(f"mean |gap| full sample = {np.abs(gap).mean():.2f}pp  corr(rule,actual)={np.corrcoef(rule,actual)[0,1]:.3f}")
for dec in range(1960, 2030, 10):
    sel = (x >= dec) & (x < dec + 10)
    if sel.sum():
        print(f"decade {dec}s: mean gap {gap[sel].mean():+.2f}pp  mean |gap| {np.abs(gap[sel]).mean():.2f}pp")
sel = (x >= 2021) & (x < 2023)
i = np.argmax(gap * sel)
print(f"max gap 2021-22: {gap[i]:+.2f}pp in {months[i]} (rule {rule[i]:.2f} vs actual {actual[i]:.2f})")
sel = (x >= 1975) & (x < 1976)
print(f"mean gap 1975: {gap[sel].mean():+.2f}pp")
sel = (x >= 2009) & (x < 2016)
print(f"mean gap 2009-2015 (ZLB): {gap[sel].mean():+.2f}pp (rule below zero share: {(rule[sel]<0).mean()*100:.0f}%)")
