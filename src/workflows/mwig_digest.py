"""mWIG40 daily trader-vibe digest."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel

import mistralai.workflows as workflows
from mistralai.workflows.client import get_mistral_client

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

DIGEST_MODEL = os.environ.get("DIGEST_MODEL", "mistral-medium-latest")
WARSAW = timezone(timedelta(hours=1))

STOOQ_SYMBOLS = {
    "mWIG40": "^mwig",
    "WIG20": "^wig20",
    "EURPLN": "eurpln",
}

RSS_FEEDS = [
    "https://www.rmf24.pl/fakty/polska/feed",
    "https://www.bankier.pl/rss/wiadomosci.xml",
    "https://www.bankier.pl/rss/gielda.xml",
    "https://parkiet.com/rss/najnowsze.xml",
    "https://www.pb.pl/rss/v2/holdings-gpw.xml",
    "https://www.analizy.pl/rss/analizygpw.xml",
]

SYSTEM_PROMPT = """You are 'Gordon', a veteran Warsaw-equity trading-desk editor with a Bloomberg-terminal soul and
stand-up timing. You write ONE daily digest in English for a young Polish retail investor
who holds the Beta ETF mWIG40TR (Polish mid-caps) and VWCE (global equities), invests monthly,
loves trading lore, and wants to build real market instincts.

Rules:
- Base EVERYTHING strictly on the DATA BLOCK provided. Never invent prices, names or events.
  If the data is thin, say so and lean on education instead of fabricating news.
- Translate Polish headlines to English; cite source name in brackets like [Parkiet].
- Tone: punchy, fun, trader-slang-rich, but zero financial advice and no 'buy/sell' calls.
- Structure (exact sections, keep tight, max ~700 words total):
  THE TAPE - index close + % change, WIG20 for breadth, EUR/PLN, one-line read of the mood.
  MOVER SPOTLIGHT - pick the single juiciest headline(s) and explain WHY it moves mid-caps.
  INSIDER WHISPERS - analyst chatter, results, dividend/block-trade signals from headlines.
  WHY IT MATTERS FOR YOU - connect the day to a monthly mWIG40TR buyer (news informs dates, not impulses).
  TRADER LINGO - one term taught per day with a tiny Warsaw-market example.
  FUN FACT - a real, verifiable market-history tidbit; prefer Poland/GPW trivia.
- Plain text formatting with emoji section headers and short lines."""


class DigestInput(BaseModel):
    date: str | None = None
    force_send: bool = True


def _http_get(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) mwig-daily-digest/0.1"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _http_post_json(url: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


@workflows.activity(
    start_to_close_timeout=timedelta(minutes=3),
    retry_policy_max_attempts=3,
    retry_policy_backoff_coefficient=2.0,
)
async def fetch_market_data(input: DigestInput) -> dict[str, Any]:
    ref = datetime.strptime(input.date, "%Y-%m-%d").date() if input.date else datetime.now(WARSAW).date()
    d2 = ref.strftime("%Y%m%d")
    d1 = (ref - timedelta(days=14)).strftime("%Y%m%d")
    out: dict[str, Any] = {"ref_date": ref.isoformat()}
    for name, sym in STOOQ_SYMBOLS.items():
        try:
            csv_text = _http_get(stooq_history_url(sym, d1, d2))
            rows = parse_stooq_csv(csv_text)
            out[name] = last_change(rows)
        except Exception as exc:  # noqa: BLE001
            out[name] = {"error": f"{type(exc).__name__}: {exc}"}
    return out


@workflows.activity(
    start_to_close_timeout=timedelta(minutes=3),
    retry_policy_max_attempts=3,
    retry_policy_backoff_coefficient=2.0,
)
async def fetch_news(input: DigestInput) -> dict[str, Any]:
    collected: list[dict[str, str]] = []
    feeds_ok: list[str] = []
    for feed in RSS_FEEDS:
        try:
            items = extract_rss_items(_http_get(feed), limit=8)
            if items:
                name = feed.split("/")[2]
                for it in items:
                    it["source"] = name
                collected.extend(items)
                feeds_ok.append(name)
        except Exception:  # noqa: BLE001
            continue
    ranked = score_market_relevance(collected)[:25]
    return {"feeds": feeds_ok, "items": ranked}


@workflows.activity(
    start_to_close_timeout=timedelta(minutes=6),
    retry_policy_max_attempts=2,
    retry_policy_backoff_coefficient=2.0,
)
async def generate_digest(market: dict[str, Any], news: dict[str, Any]) -> str:
    data_block = json.dumps({"market": market, "news": news}, ensure_ascii=False, indent=2)
    client = get_mistral_client()
    resp = await client.chat.complete_async(
        model=DIGEST_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "DATA BLOCK (today, Warsaw time):\n" + data_block + "\n\nWrite today's digest now."},
        ],
        temperature=0.7,
        max_tokens=1600,
    )
    return resp.choices[0].message.content or ""


@workflows.activity(
    start_to_close_timeout=timedelta(minutes=2),
    retry_policy_max_attempts=3,
    retry_policy_backoff_coefficient=2.0,
)
async def send_telegram(digest_text: str, input: DigestInput) -> dict[str, Any]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return {"sent": False, "reason": "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set"}
    sent: list[int] = []
    chunks = split_for_telegram(digest_text)
    for i, chunk in enumerate(chunks):
        payload = {
            "chat_id": chat_id,
            "text": sanitize_for_html(chunk),
            "disable_web_page_preview": True,
        }
        if len(chunks) > 1:
            payload["text"] = f"({i + 1}/{len(chunks)}) " + payload["text"]
        result = _http_post_json(
            f"https://api.telegram.org/bot{token}/sendMessage",
            payload,
        )
        sent.append(int(result.get("message_id", 0)))
    return {"sent": True, "message_ids": sent, "chunks": len(chunks)}


@workflows.workflow.define(
    name="mwig-daily-digest",
    workflow_display_name="mWIG40 Daily Digest",
    workflow_description="Daily 18:15 Europe/Warsaw trader-vibe digest of the Polish mWIG40 session, pushed to Telegram.",
)
class MwigDailyDigestWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: DigestInput) -> dict[str, Any]:
        market = await fetch_market_data(input)
        news = await fetch_news(input)
        digest = await generate_digest(market, news)
        delivery = await send_telegram(digest, input)
        summary_bits = []
        for name in ("mWIG40", "WIG20", "EURPLN"):
            m = market.get(name) or {}
            if isinstance(m, dict) and "pct" in m:
                summary_bits.append(f"{name} {format_pct(m.get('pct'))}")
        return {
            "digest_chars": len(digest),
            "market_summary": " | ".join(summary_bits),
            "telegram": delivery,
        }
