"""
fig_e1_build_caches.py - provision the FRED-format data caches for the E1
figures from ALTERNATIVE authoritative sources, when fred.stlouisfed.org is
unreachable from the build machine.

Every FRED series used by the E1 figure scripts is mirrored, byte-for-byte in
its published values, by the *primary* agency that FRED itself redistributes.
This script pulls each series from that primary agency and writes a cache file
in the exact FRED CSV shape the figure scripts expect
(``observation_date,<ID>`` header, ``YYYY-MM-DD,value`` rows, missing = "."),
so the unmodified fig_e1_*.py scripts run offline against these caches. If FRED
is reachable again, deleting a cache lets the original script re-fetch it and
reproduce the identical figure.

Source map (primary agency FRED mirrors):
  CPIAUCSL   -> BLS series CUSR0000SA0     (api.bls.gov, keyless v1)
  CPILFESL   -> BLS series CUSR0000SA0L1E  (api.bls.gov, keyless v1)
  T10Y2Y     -> Fed H.15 (10y CMT - 2y CMT), federalreserve.gov datadownload
  T10Y3M     -> Fed H.15 (10y CMT - 3m CMT), federalreserve.gov datadownload
  USREC      -> NBER business-cycle peak/trough dates (public constants)
  DFEDTARU   -> FRBNY EFFR API targetRateTo (markets.newyorkfed.org)
  FEDFUNDS   -> Fed H.15 effective fed funds monthly (see fig_e1_build_caches2)
  WALCL      -> Fed H.4.1 total assets (see fig_e1_build_caches2)
  INDPRO     -> Fed G.17 industrial production (see fig_e1_build_caches2)
  A191RL1Q225SBEA -> real GDP % SAAR (see fig_e1_build_caches2)

Run:  python fig_e1_build_caches.py     # stdlib only (urllib, json, csv)
"""
import os, io, csv, json, socket, urllib.request, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# Offline-deterministic: if every cache this builder provides already exists, do
# nothing -- no network fetch, no overwrite (which is what drifted the repo when
# the figure harness re-ran the builders). Delete a cache file to force a re-fetch.
_OUT = ["CPIAUCSL", "CPILFESL", "T10Y2Y", "T10Y3M", "USREC", "DFEDTARU"]
if all(os.path.exists(os.path.join(DATA, s + ".csv")) for s in _OUT):
    print("SKIPPED fig_e1_build_caches: all caches present (delete one to re-fetch).")
    raise SystemExit(0)
os.makedirs(DATA, exist_ok=True)
socket.setdefaulttimeout(60)


def _get(url, data=None, headers=None):
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    last = None
    for _ in range(4):
        try:
            return urllib.request.urlopen(req).read()
        except Exception as e:                       # noqa: BLE001
            last = e
    raise last


def write_cache(series_id, rows):
    """rows: list of (datetime, value_str_or_None); write FRED-shape CSV atomically."""
    rows = sorted(rows, key=lambda r: r[0])
    path = os.path.join(DATA, series_id + ".csv")
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["observation_date", series_id])
        for d, v in rows:
            w.writerow([d.strftime("%Y-%m-%d"), "." if v is None else v])
    os.replace(tmp, path)
    print(f"wrote {series_id}.csv  n={len(rows)}  "
          f"{rows[0][0]:%Y-%m}..{rows[-1][0]:%Y-%m}")


# --------------------------------------------------------------------------- #
# 1) BLS: CPIAUCSL (headline) and CPILFESL (core), monthly, seasonally adj.
# --------------------------------------------------------------------------- #
def bls_series(bls_id, y0, y1):
    """Fetch one BLS series across [y0,y1] in <=10y chunks (keyless v1)."""
    out = {}
    a = y0
    while a <= y1:
        b = min(a + 9, y1)
        payload = json.dumps({"seriesid": [bls_id],
                              "startyear": str(a), "endyear": str(b)}).encode()
        raw = _get("https://api.bls.gov/publicAPI/v1/timeseries/data/",
                   data=payload, headers={"Content-Type": "application/json"})
        d = json.loads(raw)
        if d.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS {bls_id} {a}-{b}: {d.get('message')}")
        for rec in d["Results"]["series"][0]["data"]:
            p = rec["period"]
            if not p.startswith("M") or p == "M13":     # skip annual avg
                continue
            mo = int(p[1:])
            val = rec["value"]
            try:
                float(val)                              # BLS uses "-" for N/A
            except (ValueError, TypeError):
                val = None
            out[dt.datetime(int(rec["year"]), mo, 1)] = val
        a = b + 1
    return [(k, v) for k, v in out.items()]


write_cache("CPIAUCSL", bls_series("CUSR0000SA0", 1969, 2026))
write_cache("CPILFESL", bls_series("CUSR0000SA0L1E", 2016, 2026))


# --------------------------------------------------------------------------- #
# 2) Fed H.15 constant-maturity Treasury yields -> T10Y2Y, T10Y3M (daily)
#    Package hex = Treasury CMT block; series order (after date):
#    1mo,3mo,6mo,1y,2y,3y,5y,7y,10y,20y,30y
# --------------------------------------------------------------------------- #
def h15_cmt(y0=1976, y1=2026):
    url = ("https://www.federalreserve.gov/datadownload/Output.aspx?"
           "rel=H15&series=bf17364827e38702b42a58cf8eaa3f78&lastobs="
           f"&from=01/01/{y0}&to=12/31/{y1}"
           "&filetype=csv&label=include&layout=seriescolumn")
    raw = _get(url).decode("utf-8", "replace")
    rdr = csv.reader(io.StringIO(raw))
    body = list(rdr)[6:]                 # 6 metadata rows, then data
    yld = {}                             # date -> {'10y','2y','3m'}
    for row in body:
        if len(row) < 12 or not row[0]:
            continue
        try:
            d = dt.datetime.strptime(row[0], "%Y-%m-%d")
        except ValueError:
            continue
        def num(i):
            try:
                return float(row[i])
            except (ValueError, IndexError):
                return None
        yld[d] = {"3m": num(2), "2y": num(5), "10y": num(9)}
    return yld


yld = h15_cmt()
t10y2y = [(d, f"{v['10y'] - v['2y']:.2f}") for d, v in yld.items()
          if v["10y"] is not None and v["2y"] is not None]
t10y3m = [(d, f"{v['10y'] - v['3m']:.2f}") for d, v in yld.items()
          if v["10y"] is not None and v["3m"] is not None]
write_cache("T10Y2Y", t10y2y)
write_cache("T10Y3M", t10y3m)


# --------------------------------------------------------------------------- #
# 3) USREC - NBER business-cycle recession indicator, monthly.
#    FRED convention: 1 for the months FOLLOWING the peak through the trough.
#    NBER peak/trough dates (public record, nber.org/cycles).
# --------------------------------------------------------------------------- #
NBER = [  # (peak year, month), (trough year, month)
    ((1948, 11), (1949, 10)),
    ((1953, 7),  (1954, 5)),
    ((1957, 8),  (1958, 4)),
    ((1960, 4),  (1961, 2)),
    ((1969, 12), (1970, 11)),
    ((1973, 11), (1975, 3)),
    ((1980, 1),  (1980, 7)),
    ((1981, 7),  (1982, 11)),
    ((1990, 7),  (1991, 3)),
    ((2001, 3),  (2001, 11)),
    ((2007, 12), (2009, 6)),
    ((2020, 2),  (2020, 4)),
]


def month_iter(a, b):
    y, m = a
    while (y, m) <= b:
        yield dt.datetime(y, m, 1)
        m += 1
        if m == 13:
            y += 1; m = 1


rec_flag = {}
for (py, pm), (ty, tm) in NBER:
    # months strictly after the peak, through and including the trough
    start = (py + (pm == 12), 1 if pm == 12 else pm + 1)
    for d in month_iter(start, (ty, tm)):
        rec_flag[d] = 1
usrec = [(d, str(rec_flag.get(d, 0))) for d in month_iter((1948, 1), (2026, 9))]
write_cache("USREC", usrec)


# --------------------------------------------------------------------------- #
# 4) DFEDTARU - fed funds target range, upper limit, daily.
#    FRBNY EFFR API publishes targetRateTo per business day (self-correcting
#    for 2025-26 decisions). Chunk by <=1yr to avoid response caps.
# --------------------------------------------------------------------------- #
def nyfed_target(y0=2008, y1=2026):
    out = {}
    for y in range(y0, y1 + 1):
        url = ("https://markets.newyorkfed.org/api/rates/unsecured/effr/"
               f"search.json?startDate={y}-01-01&endDate={y}-12-31")
        d = json.loads(_get(url))
        for r in d.get("refRates", []):
            if r.get("type") != "EFFR":
                continue
            tr = r.get("targetRateTo")
            if tr is None:
                continue
            out[dt.datetime.strptime(r["effectiveDate"], "%Y-%m-%d")] = f"{float(tr):.2f}"
    return [(k, v) for k, v in out.items()]


write_cache("DFEDTARU", nyfed_target())
print("done: confirmed-source caches")
