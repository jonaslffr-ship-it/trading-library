"""
fig_e1_build_caches2.py - the Fed-only and GDP caches for the E1 figures,
from primary sources, since fred.stlouisfed.org is unreachable at build time.
Companion to fig_e1_build_caches.py. Writes FRED-shape caches to data/.

  FEDFUNDS  -> Fed H.15, effective fed funds rate, monthly (RIFSPFF_N.M)
  WALCL     -> Fed H.4.1, total assets Wednesday level, weekly (RESPPMA_N.WW, $M)
  INDPRO    -> Fed G.17 release file ip_sa.txt, Total Index (B50001), 2017=100
  A191RL1Q225SBEA -> OECD quarterly real GDP growth (QoQ), annualized to SAAR.
                     NOTE: OECD's seasonal adjustment / chain-linking differs
                     marginally from BEA's own A191RL1Q225SBEA; the COVID
                     quarters match to a few tenths. Disclosed in the paper.

Run:  python fig_e1_build_caches2.py     # stdlib only
"""
import os, io, csv, socket, urllib.request, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# Offline-deterministic: if every cache this builder provides already exists, do
# nothing -- no network fetch, no overwrite. Delete a cache file to force a re-fetch.
_OUT = ["FEDFUNDS", "WALCL", "INDPRO", "A191RL1Q225SBEA"]
if all(os.path.exists(os.path.join(DATA, s + ".csv")) for s in _OUT):
    print("SKIPPED fig_e1_build_caches2: all caches present (delete one to re-fetch).")
    raise SystemExit(0)
os.makedirs(DATA, exist_ok=True)
socket.setdefaulttimeout(90)


def _get(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    last = None
    for _ in range(4):
        try:
            return urllib.request.urlopen(req).read()
        except Exception as e:                       # noqa: BLE001
            last = e
    raise last


def write_cache(series_id, rows):
    rows = sorted(rows, key=lambda r: r[0])
    path = os.path.join(DATA, series_id + ".csv")
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["observation_date", series_id])
        for d, v in rows:
            w.writerow([d.strftime("%Y-%m-%d"), "." if v is None else v])
    os.replace(tmp, path)
    print(f"wrote {series_id}.csv  n={len(rows)}  {rows[0][0]:%Y-%m}..{rows[-1][0]:%Y-%m}")


def ddp_rows(raw):
    """Yield data rows of a Fed DDP CSV (6 metadata rows, then data). Also
    return the header ('Time Period') row for column lookup."""
    rdr = list(csv.reader(io.StringIO(raw.decode("utf-8", "replace"))))
    header = rdr[5]          # row 6: "Time Period","CODE",...
    return header, rdr[6:]


# --------------------------------------------------------------------------- #
# FEDFUNDS - H.15 effective fed funds, monthly (single-series package)
# --------------------------------------------------------------------------- #
raw = _get("https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&"
           "series=40afb80a445c5903ca2c4888e40f3f1f&lastobs=&from=&to="
           "&filetype=csv&label=include&layout=seriescolumn")
_, body = ddp_rows(raw)
ff = []
for row in body:
    if len(row) < 2 or not row[0]:
        continue
    v = row[1]
    ff.append((dt.datetime.strptime(row[0] + "-01", "%Y-%m-%d"),
               None if v.strip() in ("ND", "") else v.strip()))
write_cache("FEDFUNDS", ff)


# --------------------------------------------------------------------------- #
# WALCL - H.4.1 total assets, weekly Wednesday level ($ millions).
# Locate the RESPPMA_N.WW column by name in the header row.
# --------------------------------------------------------------------------- #
raw = _get("https://www.federalreserve.gov/datadownload/Output.aspx?rel=H41&"
           "series=efce2c1a8744855f2623889dffb2b39a&from=01/01/2002&to=12/31/2026"
           "&filetype=csv&label=include&layout=seriescolumn")
header, body = ddp_rows(raw)
try:
    col = header.index("RESPPMA_N.WW")
except ValueError:                                    # fall back to reported col 24
    col = 23
bs = []
for row in body:
    if len(row) <= col or not row[0]:
        continue
    v = row[col]
    bs.append((dt.datetime.strptime(row[0], "%Y-%m-%d"),
               None if v.strip() in ("ND", "") else v.strip()))
write_cache("WALCL", bs)


# --------------------------------------------------------------------------- #
# INDPRO - G.17 release file, Total Index (B50001), SA, 2017=100.
# Whitespace layout: "B50001"  YEAR  jan feb ... dec  (current year partial).
# --------------------------------------------------------------------------- #
txt = _get("https://www.federalreserve.gov/releases/g17/Current/ipdisk/ip_sa.txt")
ip = []
for line in txt.decode("utf-8", "replace").splitlines():
    parts = line.split()
    if not parts or parts[0].strip('"') != "B50001":
        continue
    year = int(parts[1])
    for m, val in enumerate(parts[2:14], start=1):    # up to 12 months
        try:
            float(val)
        except ValueError:
            continue
        ip.append((dt.datetime(year, m, 1), val))
write_cache("INDPRO", ip)


# --------------------------------------------------------------------------- #
# A191RL1Q225SBEA - OECD quarterly real GDP growth (QoQ %) -> annualize to SAAR.
# --------------------------------------------------------------------------- #
raw = _get("https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,"
           "DSD_NAMAIN1@DF_QNA_EXPENDITURE_GROWTH_OECD/Q..USA...B1GQ......G1."
           "?dimensionAtObservation=AllDimensions&format=csvfilewithlabels")
rdr = csv.reader(io.StringIO(raw.decode("utf-8", "replace")))
head = next(rdr)
i_t, i_v = head.index("TIME_PERIOD"), head.index("OBS_VALUE")
QM = {"Q1": 1, "Q2": 4, "Q3": 7, "Q4": 10}
gdp = []
for row in rdr:
    if len(row) <= max(i_t, i_v):
        continue
    tp, ov = row[i_t].strip(), row[i_v].strip()
    if "-Q" not in tp or ov == "":
        continue
    y, q = tp.split("-")
    if q not in QM:
        continue
    saar = ((1.0 + float(ov) / 100.0) ** 4 - 1.0) * 100.0   # annualize QoQ
    gdp.append((dt.datetime(int(y), QM[q], 1), f"{saar:.1f}"))
write_cache("A191RL1Q225SBEA", gdp)
print("done: Fed-only + GDP caches")
