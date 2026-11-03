"""Pure stdlib helpers: stooq CSV parsing, RSS extraction, Telegram chunking."""

from __future__ import annotations

import csv
import io
import xml.etree.ElementTree as ET
from typing import Any


def parse_stooq_csv(text: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(io.StringIO(text.strip())))
    return rows


def last_change(rows: list[dict[str, str]]) -> dict[str, Any] | None:
    if not rows:
        return None
    last = rows[-1]
    prev = rows[-2] if len(rows) >= 2 else None
    try:
        close = float(last["Close"])
    except (KeyError, ValueError, TypeError):
        return None
    pct = None
    if prev is not None:
        try:
            p = float(prev["Close"])
            if p != 0:
                pct = round((close / p - 1.0) * 100.0, 2)
        except (KeyError, ValueError, TypeError):
            pass
    return {"date": last.get("Date", ""), "close": close, "pct": pct}


def extract_rss_items(xml_text: str, limit: int = 6) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    def _txt(el: ET.Element | None) -> str:
        return (el.text or "").strip() if el is not None and el.text else ""

    for it in root.iter("item"):
        title = _txt(it.find("title"))
        link = _txt(it.find("link"))
        pub = _txt(it.find("pubDate"))
        if title:
            items.append({"title": title, "link": link, "published": pub})
        if len(items) >= limit:
            return items

    ns = "{http://www.w3.org/2005/Atom}"
    if not items:
        for it in root.iter(ns + "entry"):
            title = _txt(it.find(ns + "title"))
            link_el = it.find(ns + "link")
            link = link_el.get("href", "") if link_el is not None else ""
            pub = _txt(it.find(ns + "updated"))
            if title:
                items.append({"title": title, "link": link, "published": pub})
            if len(items) >= limit:
                break
    return items[:limit]


_MARKET_KEYWORDS = (
    "mwig", "wig40", "wig20", "swig80", "wig", "gpw", "gie\u0142da", "akcje",
    "indeks", "parkiet", "santander", "kghm", "pko", "pekao", "orange",
    "lotos", "budimex", "bytom", "play", "dsv", "inpost",
    "akcjonariusz", "dywidenda", "dividend", "wyniki", "raport", "cpi",
    "inflac", "nbp", "rpp", "stop", "z\u0142oty", "eur/pln", "sankcj", "ce\u0142",
    "ceny", "paliw", "energi", "obligacj", "bud\u017cet", "pkb", "gdp",
)


def score_market_relevance(items: list[dict[str, str]]) -> list[dict[str, str]]:
    def score(it: dict[str, str]) -> int:
        t = it.get("title", "").lower()
        return sum(1 for kw in _MARKET_KEYWORDS if kw in t)
    return sorted(items, key=score, reverse=True)


def split_for_telegram(text: str, max_len: int = 3900) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    rest = text
    while len(rest) > max_len:
        cut = rest.rfind("\n\n", 0, max_len)
        if cut == -1 or cut < max_len // 2:
            cut = rest.rfind("\n", 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(rest[:cut])
        rest = rest[cut:].lstrip("\n")
    if rest:
        chunks.append(rest)
    return chunks


def format_pct(pct: float | None) -> str:
    if pct is None:
        return "\u2014"
    arrow = "\U0001F7E2" if pct > 0 else ("\U0001F534" if pct < 0 else "\u26AA\uFE0F")
    return f"{arrow} {pct:+.2f}%"


def sanitize_for_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def stooq_history_url(symbol: str, d1: str, d2: str) -> str:
    return f"https://stooq.com/q/d/l/?s={symbol}&d1={d1}&d2={d2}&i=d"
