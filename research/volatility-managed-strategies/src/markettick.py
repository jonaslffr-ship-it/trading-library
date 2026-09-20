"""MarketTick API client — fetch the download catalog, then download & extract files.

Design
------
The link-overview page embeds the full download catalog as a base64-encoded JSON blob
in ``<div id="downloads-base64">...</div>``. Decoding it yields, per file, the download
URL *and* its per-file unzip password — so we never hardcode URL patterns or passwords,
and index-candle links work the same way as futures links.

Secrets
-------
The API key is read from the environment variable ``MARKETTICK_APIKEY``. It is NEVER
hardcoded or committed. Raw data downloaded here is licensed and must stay out of git
(see ``.gitignore``: ``data/raw/**``). Refresh the key in your MarketTick account.

Note
----
The exact JSON field names are confirmed on the first run against a valid key
(``--schema``). Field access below is deliberately schema-tolerant.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.request
from pathlib import Path

LINKS_URL = "https://markettick.net/mt_api/data-buy_links.php?apikey={key}"
_BLOB_RE = re.compile(r'id=["\']downloads-base64["\'][^>]*>([^<]*)<', re.I)


def get_apikey() -> str:
    key = os.environ.get("MARKETTICK_APIKEY", "").strip()
    if not key:
        raise RuntimeError(
            "Set MARKETTICK_APIKEY (env var). Get a fresh key from your MarketTick account."
        )
    return key


def parse_catalog(html: str) -> list:
    """Extract + base64-decode the embedded download catalog to a list of dicts."""
    m = _BLOB_RE.search(html)
    if not m:
        raise RuntimeError("downloads-base64 blob not found (invalid key or page changed?)")
    raw = base64.b64decode(m.group(1)).decode("utf-8", "replace")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise RuntimeError(f"unexpected catalog type: {type(data).__name__}")
    return data


def fetch_catalog(apikey: str = None, timeout: int = 60) -> list:
    apikey = apikey or get_apikey()
    with urllib.request.urlopen(LINKS_URL.format(key=apikey), timeout=timeout) as r:
        html = r.read().decode("utf-8", "replace")
    if "not valid" in html.lower():
        raise RuntimeError("MarketTick API key is not valid — refresh it in your account.")
    return parse_catalog(html)


def _g(entry: dict, *keys, default=None):
    """Return the first present, non-empty key (schema-tolerant)."""
    for k in keys:
        if k in entry and entry[k] not in (None, ""):
            return entry[k]
    return default


def find(catalog, symbol=None, level=None, date=None) -> list:
    """Filter catalog entries (case-insensitive symbol/level, exact date)."""
    hits = []
    for e in catalog:
        if symbol and str(_g(e, "symbol", "sym", default="")).upper() != symbol.upper():
            continue
        if level and str(_g(e, "level", "type", default="")).upper() != str(level).upper():
            continue
        if date and str(_g(e, "date", "month", "year", default="")) != str(date):
            continue
        hits.append(e)
    return hits


def download_and_extract(entry: dict, dest_dir="data/raw", timeout: int = 600) -> Path:
    """Download the entry's archive and extract it with its per-file password."""
    url = _g(entry, "download_url", "url", "link")
    pw = _g(entry, "unzip_password", "password", "pw")
    if not url:
        raise RuntimeError(f"no download url in entry (keys: {list(entry)[:8]})")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    name = _g(entry, "filename", "file") or url.split("/")[-1].split("?")[0] or "mt_download"
    archive = dest / name
    with urllib.request.urlopen(url, timeout=timeout) as r, open(archive, "wb") as f:
        f.write(r.read())
    _extract(archive, dest, pw)
    return dest


def _extract(archive: Path, dest: Path, password):
    suffix = archive.suffix.lower()
    if suffix == ".7z":
        import py7zr  # pip install py7zr
        with py7zr.SevenZipFile(archive, mode="r", password=password) as z:
            z.extractall(path=dest)
    elif suffix == ".zip":
        import zipfile
        with zipfile.ZipFile(archive) as z:
            z.extractall(path=dest, pwd=password.encode() if password else None)
    else:
        raise RuntimeError(f"unknown archive type: {suffix!r}")


def _cli():
    ap = argparse.ArgumentParser(description="MarketTick catalog downloader")
    ap.add_argument("--schema", action="store_true", help="print keys of the first catalog entry")
    ap.add_argument("--list", metavar="SYMBOL", help="list available files for a symbol")
    ap.add_argument("--download", metavar="SYMBOL", help="symbol to download")
    ap.add_argument("--date", help="YYYY (index candles) or YYYYMM (futures)")
    ap.add_argument("--level", help="e.g. T2 for futures; candle level for indices")
    ap.add_argument("--dest", default="data/raw")
    args = ap.parse_args()

    cat = fetch_catalog()
    print(f"catalog entries: {len(cat)}")
    if args.schema and cat:
        print("first entry keys:", list(cat[0].keys()))
        return
    if args.list:
        for e in find(cat, symbol=args.list):
            print(_g(e, "symbol"), _g(e, "level", "type"), _g(e, "date", "month", "year"))
        return
    if args.download:
        hits = find(cat, symbol=args.download, level=args.level, date=args.date)
        if not hits:
            print("no matching file — try --list", args.download); return
        print("extracted into", download_and_extract(hits[0], args.dest))


if __name__ == "__main__":
    _cli()
