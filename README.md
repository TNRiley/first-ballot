# 🌟 First Ballot

**Every lead and supporting acting Emmy nomination since 1979, and who never got the envelope. 72.5% never won it. Of the ones who did, 68% won on their first try.**

→ **[Open it](https://tnriley.github.io/first-ballot/)**

A 2026 Emmy CSV compiled by a fan project, regrouped into twelve lead/supporting × actor/actress × drama/comedy/limited-series categories — 1,573 acting careers, 1979 through the 78th Emmys on September 14, 2026. The news said Matthew Rhys became the first person to win two lead-actor Emmys in one year; checked against the full history, that's true only because it says ‘lead’ — James Earl Jones (1991) and Stockard Channing (2002) each won two of these categories in a single year too, just not two Lead ones. The bigger pattern: 72.5% of everyone ever nominated in these categories since 1979 never won, and of the 27% who did, 68% won on their very first nomination — a second or third try barely moves the odds. Angela Lansbury holds the all-time drought record, twelve straight Lead Actress–Drama nominations for Murder, She Wrote with zero wins, nearly double the next-longest streak. Every person's nomination history is browsable by category, dot for dot, win or loss.

## Running it

One self-contained HTML file. No build step, no server, no network access at runtime — open `index.html` in a browser, or serve the directory with any static host.

```bash
python3 -m http.server 8000   # then visit http://localhost:8000
```

## Rebuilding it from scratch

[REBUILD.md](REBUILD.md) is written for an LLM with a shell and nothing else: the data sources and their quirks, the processing decisions, the page's structure and interactions, and a table of expected values to check the result against.

## Source

The full build pipeline is in [`src/`](src/), with a README describing how to regenerate the page from scratch.

## Data

- **[emmys-data (dmase2), a compiled Primetime Emmy nominations CSV, 1949–2026](https://github.com/dmase2/emmys-data)** — No licence file published; the underlying facts (nominee, category, year, winner) are historical record of the Television Academy's own public awards, not the compiler's creative expression.

Every figure on the page is computed from the data shipped with it. Check the page's own methods panel for how each number is derived and where it should not be pushed.

## Built with

python 3 stdlib, keyword category classifier, vanilla JS, inline SVG, JSON payload.

## Licence

Code is MIT (see [LICENSE](LICENSE)). Data keeps the licence of its source, listed above.

---

Part of [Quick Projects](https://github.com/TNRiley/quick-projects) — one self-contained thing, built in one session. First published 2026-09-22.
