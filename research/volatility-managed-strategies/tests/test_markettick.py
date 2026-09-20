"""Catalog parsing/filtering tests for the MarketTick client (no network)."""
from __future__ import annotations

import base64
import json

from src.markettick import parse_catalog, find, _g


def _fake_page(entries):
    blob = base64.b64encode(json.dumps(entries).encode()).decode()
    return f'<div id="downloads-base64" style="display:none">{blob}</div>'


def test_parse_catalog_roundtrip():
    entries = [
        {"symbol": "SP500", "level": "candle1m", "date": "2024",
         "download_url": "https://host/SP500_2024.7z", "unzip_password": "pw1"},
        {"symbol": "ES", "level": "T2", "date": "202406",
         "download_url": "https://host/ES_202406.7z", "unzip_password": "pw2"},
    ]
    cat = parse_catalog(_fake_page(entries))
    assert cat == entries


def test_find_and_getter():
    entries = [{"symbol": "SP500", "level": "candle1m", "date": "2024",
                "url": "https://host/x.7z", "password": "pw"}]
    cat = parse_catalog(_fake_page(entries))
    assert find(cat, symbol="sp500")          # case-insensitive
    assert not find(cat, symbol="NQ")
    assert _g(cat[0], "download_url", "url") == "https://host/x.7z"
    assert _g(cat[0], "unzip_password", "password") == "pw"
