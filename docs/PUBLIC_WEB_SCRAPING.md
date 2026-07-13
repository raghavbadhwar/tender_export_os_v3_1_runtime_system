# Public Web Scraping and Evidence Capture

Tender Export OS now has four complementary public-web lanes:

1. **Discovery** — Hermes `web_search` uses the no-key DDGS backend; ChatGPT Deep Research handles broad multi-source market judgment.
2. **Static scraping** — `scripts/public_web_evidence_scraper.py` extracts public HTML into raw HTML, visible text, structured JSON, links, headings, public `mailto:` contacts, hashes, and a run receipt.
3. **JavaScript rendering** — `scripts/agent_browser_capture.py` captures JS-rendered pages with agent-browser, including snapshot, page text, screenshot, hashes, blockers, and receipt.
4. **Known portals** — GeM, CPPP, UNGM, and configured sources use the dedicated adapters and selector contracts.

## Static scraping example

```bash
.venv/bin/python scripts/public_web_evidence_scraper.py \
  --url "https://example.com/catalogue" \
  --source-name "Example catalogue" \
  --follow-links \
  --max-pages 10 \
  --max-depth 1
```

For multiple known URLs, repeat `--url` or pass `--urls-file`. A file contains one URL per line; blank lines and lines beginning with `#` are ignored.

## Safety and evidence contract

- Public HTTPS targets only; local/private/reserved targets are rejected.
- `robots.txt` is enforced and failures are fail-closed.
- Same-host link following only, minimum one-second delay, maximum 50 pages and depth 3 per run.
- HTML response size is bounded; document/media suffixes are not recursively crawled.
- Redirects to another host are rejected.
- Page text is untrusted evidence and never treated as instructions.
- No login, cookies, CAPTCHA/paywall bypass, forms, click, upload, message, payment, DSC, or commercial commitment.
- Public contacts are routing evidence only; no guessed personal emails or automatic outreach.
- Catalogue fit remains a demand hypothesis until a buyer reply, RFQ, order, or comparable proof confirms it.

Canonical policy: `config/public_web_scraping.yaml`. New raw HTML, browser
snapshots, screenshots, extracted text, and receipts default to
`outputs/evidence/private/`; only deliberately redacted artifacts may be
published outside that private evidence root.

Verified canary on 2026-07-12: the official Hermes documentation page returned HTTP 200 with robots allowed; raw HTML, extracted JSON/text, 10 headings, 44 links, and SHA-256 hashes were stored under `outputs/web_scraping/WEB-20260712T000400Z-fd621c81/`.

Hermes itself loaded `teos-public-web-scraping`, inspected that receipt through a local read-only tool, and returned `SCRAPING_CAPABILITY_OK captured=1 robots=true external_actions=false`. The DDGS-backed Hermes web tool separately returned the canonical official documentation URL.
