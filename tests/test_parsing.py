"""Stdlib-only unit tests for parsing helpers. Run: python3 tests/test_parsing.py"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "workflows")))

from parsing import (
    extract_rss_items,
    format_pct,
    last_change,
    parse_stooq_csv,
    sanitize_for_html,
    score_market_relevance,
    split_for_telegram,
    stooq_history_url,
)

csv_text = "Date,Open,High,Low,Close,Volume\n2026-10-30,100,102,99,101,1000\n2026-11-03,101,105,100,104,1500\n"
rows = parse_stooq_csv(csv_text)
assert len(rows) == 2, rows
lc = last_change(rows)
assert lc is not None
assert abs(lc["pct"] - 2.97) < 0.05, lc
assert last_change([]) is None

rss = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>t</title>
<item><title>mWIG40 zyskuje po decyzji RPP</title><link>https://x/1</link><pubDate>Tue, 3 Nov 2026</pubDate></item>
<item><title>Kot zaatakowal turyste w Zakopanem</title><link>https://x/2</link></item>
</channel></rss>"""
items = extract_rss_items(rss)
assert len(items) == 2
ranked = score_market_relevance(items)
assert "mwig" in ranked[0]["title"].lower()

atom = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>t</title>
<entry><title>Atom GPW test</title><link href="https://y/1"/><updated>2026-11-03</updated></entry></feed>"""
aitems = extract_rss_items(atom)
assert len(aitems) == 1 and aitems[0]["link"] == "https://y/1"

long_text = "\n\n".join("para %d %s" % (i, "x" * 500) for i in range(30))
chunks = split_for_telegram(long_text, max_len=1000)
assert all(len(c) <= 1002 for c in chunks) and len(chunks) > 1
assert split_for_telegram("short") == ["short"]

assert format_pct(2.97).startswith("\U0001F7E2")
assert format_pct(-1.2).startswith("\U0001F534")
assert format_pct(None) == "\u2014"

assert sanitize_for_html("PKO <bp>") == "PKO &lt;bp&gt;"

url = stooq_history_url("^mwig", "20261020", "20261103")
assert url == "https://stooq.com/q/d/l/?s=^mwig&d1=20261020&d2=20261103&i=d"

print("ALL PARSING TESTS PASSED OK")
