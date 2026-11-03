# MIST-40 ULTRA — Warsaw Market Command

Personal Bloomberg-style live terminal for the Polish mWIG40 market.
Single-file app (index.html) + PWA (sw.js, manifest.webmanifest). No build step, no server, no dependencies.

## Features
- 9 desks: live board, charts (1D/5D/1M/6M/1Y), MOVERS with 24h sparklines, WORLD (FX + global indices + commodities), academy, arcade, book-sim, Gordon's desk, XP/achievements
- **TURBO feed**: the whole 35-symbol board in 2 batched Yahoo Finance requests (spark endpoint, max 20 symbols per call), progressive rendering — the board paints as soon as the first batch lands
- **Instant 1D charts** — rendered from the turbo feed, zero extra requests
- **30s auto-refresh** while the tab is visible; refreshes immediately on tab return
- **Direct ECB FX fallback** (Frankfurter API, CORS-open) when proxies are unreachable
- **Honest status badge**: LIVE / CACHED / SNAPSHOT — no fabricated data
- Embedded GPW close snapshot: the board always renders, even fully offline
- PWA: installable, amber "M40" icon, service worker keeps the shell instant and always up to date

## Run
Open `index.html` locally, or host on any static host (GitHub Pages):

```
Settings → Pages → Deploy from a branch: main, / (root)
```

URL: https://ryankibayhan.github.io/mist40-terminal/

## Files
- `index.html` — the entire app (HTML + CSS + JS, one file)
- `sw.js` — service worker (shell: stale-while-revalidate; market data: network-only)
- `manifest.webmanifest` — PWA manifest with embedded data-URI icons

## Data sources
- Quotes & series: Yahoo Finance (via public CORS proxies; batched spark endpoint)
- FX fallback: Frankfurter / ECB reference rates
- GPW snapshot embedded: close of 03 Nov 2026

Data is for personal information only. Not investment advice.
