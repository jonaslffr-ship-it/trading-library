"""
Figure - where SPX option activity lives: volume share vs. open-interest
share by days to expiry, from the cached CBOE delayed chain snapshot
(data/spx_chain_snapshot.json, same file as fig_gex_profile.py).

Volume is the snapshot day's traded contracts (the same-day expiry is
INCLUDED here - it traded all session before settling); open interest is the
end-of-day outstanding contracts. The wedge between the two bars at 0 DTE is
the measurement problem discussed in the paper: positions opened and closed
intraday never appear in any OI snapshot.

Reproducible:
    python fig_0dte_share.py     # numpy, matplotlib; stdlib json/re
"""
import os, json, re, socket, urllib.request, datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)
CACHE = os.path.join(DATA, "spx_chain_snapshot.json")
URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json"

if not os.path.exists(CACHE):
    socket.setdefaulttimeout(60)
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with open(CACHE, "wb") as f:
        f.write(urllib.request.urlopen(req).read())
chain = json.load(open(CACHE))
d = chain["data"]
snap = dt.date.fromisoformat(chain["timestamp"][:10])
pat = re.compile(r"^(SPXW?)(\d{6})([CP])(\d{8})$")

BUCKETS = [(0, 0, "0"), (1, 1, "1"), (2, 5, "2-5"), (6, 21, "6-21"),
           (22, 63, "22-63"), (64, 10 ** 6, ">63")]
vol_b = np.zeros(len(BUCKETS))
oi_b = np.zeros(len(BUCKETS))
for o in d["options"]:
    m = pat.match(o["option"])
    if not m:
        continue
    _, ymd, cp, k = m.groups()
    exp = dt.date(2000 + int(ymd[:2]), int(ymd[2:4]), int(ymd[4:6]))
    dte = (exp - snap).days
    for i, (lo, hi, _) in enumerate(BUCKETS):
        if lo <= dte <= hi:
            vol_b[i] += o["volume"]
            oi_b[i] += o["open_interest"]
            break

vshare = vol_b / vol_b.sum() * 100
oshare = oi_b / oi_b.sum() * 100
x = np.arange(len(BUCKETS))
labels = [b[2] for b in BUCKETS]

fig, ax = plt.subplots(figsize=(6.6, 4.0))
w = 0.38
b1 = ax.bar(x - w / 2, vshare, w, color="#17120e", alpha=0.9,
            label="share of day's volume")
b2 = ax.bar(x + w / 2, oshare, w, color="#8a8378", alpha=0.9,
            label="share of open interest")
for xi, v in zip(x, vshare):
    ax.text(xi - w / 2, v + 0.8, f"{v:.0f}%", ha="center", fontsize=8.2,
            color="#17120e")
for xi, v in zip(x, oshare):
    ax.text(xi + w / 2, v + 0.8, f"{v:.0f}%", ha="center", fontsize=8.2,
            color="#6b6459")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlabel("days to expiry")
ax.set_ylabel("share of SPX total (%)")
ax.set_title("SPX option volume concentrates at 0 DTE; open interest does not",
             fontsize=10.2)
ax.legend(fontsize=8.6, frameon=False)
for s_ in ("top", "right"):
    ax.spines[s_].set_visible(False)
ax.grid(True, axis="y", alpha=0.25)
fig.text(0.5, -0.02,
         f"CBOE delayed quotes {snap}: {vol_b.sum():,.0f} contracts traded, "
         f"{oi_b.sum():,.0f} open interest. 1 DTE ({snap + dt.timedelta(days=1)}) "
         f"is the September monthly OPEX, which inflates its OI share.",
         ha="center", fontsize=7.6, color="#666")
plt.tight_layout()
OUT = os.path.join(HERE, "fig_0dte_share.png")
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print("wrote", OUT)
print(f"snapshot={snap} total_volume={vol_b.sum():,.0f} total_OI={oi_b.sum():,.0f}")
for (lo, hi, lab), v, o_ in zip(BUCKETS, vshare, oshare):
    print(f"dte {lab:>6}: volume {v:5.1f}%  OI {o_:5.1f}%")
print(f"0DTE_volume_share={vshare[0]:.1f}%  0-1DTE_volume_share={vshare[0]+vshare[1]:.1f}%  "
      f"0DTE_OI_share={oshare[0]:.1f}%")
