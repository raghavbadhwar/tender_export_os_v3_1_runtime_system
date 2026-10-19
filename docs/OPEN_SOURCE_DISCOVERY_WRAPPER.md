# Open-source source discovery wrapper

This wrapper turns the local open-source search/scraping stack into a deterministic Tender Export OS evidence lane.

## Command

```bash
cd /Users/raghav/Downloads/tender_export_os_v3_1_runtime_system
.venv/bin/python scripts/run_open_source_discovery.py \
  --query "india government tender spices" \
  --workflow GOV \
  --ensure-searxng \
  --limit 8 \
  --max-pages 3 \
  --katana-depth 1 \
  --crawl4ai-limit 1
```

## Pipeline

1. **SearXNG** local metasearch at `http://127.0.0.1:8888`.
2. **DDGS** fallback search.
3. **Katana** URL expansion from discovered seed URLs.
4. **Trafilatura** HTML text extraction for detail pages.
5. **Crawl4AI** rich browser/markdown capture for a limited subset.
6. Writes an evidence-only bundle under `outputs/source_discovery/<run_id>/`.

## Outputs

Each run writes:

```text
bundle.json      machine-readable evidence bundle
bundle.md        founder/operator-readable report
manifest.json    run manifest
raw_html/        captured HTML
parsed_text/     extracted text
crawl4ai_markdown/ optional Crawl4AI markdown
```

The bundle always declares:

```json
"external_side_effects": false,
"cases_created": 0,
"approval_required_before_external_action": true
```

## Safety contract

The wrapper is **source/evidence discovery only**.

It does not:

- create cases,
- send supplier/buyer messages,
- log into portals,
- bypass access controls,
- submit bids,
- upload documents,
- commit prices/terms/origin/HS classifications.

Discovered leads remain advisory until staged through TEOS proof gates.

## Optional source-health/event recording

Use only when you want this run logged as operational source health:

```bash
.venv/bin/python scripts/run_open_source_discovery.py \
  --query "export rfq handicrafts UK buyer" \
  --workflow EXPORT \
  --record-event \
  --update-source-health
```

This uses existing schema-valid `source_adapter.*` and `source_health.updated` event types.

## Local SearXNG/Docker environment

The TEOS-local SearXNG instance uses isolated Colima/Docker state:

```bash
teos-searxng-start
export DOCKER_HOST="unix://$HOME/.colima-teos/teos/docker.sock"
export DOCKER_CONFIG="$HOME/.docker-teos"
```

The container is local-only:

```text
teos-searxng 127.0.0.1:8888->8080/tcp
```

## Fixture/offline test mode

For deterministic tests or demos:

```bash
.venv/bin/python scripts/run_open_source_discovery.py \
  --query "spice export rfq" \
  --workflow EXPORT \
  --fixture-json path/to/fixture.json \
  --output-dir outputs/source_discovery/fixture_demo
```

Fixture JSON shape:

```json
{
  "searxng": [{"title": "RFQ", "url": "https://example.test/rfq", "snippet": "..."}],
  "ddgs": [{"title": "Tender", "href": "https://example.test/tender", "body": "..."}],
  "katana": ["https://example.test/rfq/details"],
  "pages": {
    "https://example.test/rfq": "<html><article>...</article></html>"
  }
}
```

## Recommended cron/radar usage

Use the wrapper as a broad discovery scout before specialist source adapters:

1. Run 2–5 precise queries from `config/open_source_discovery_queries.yaml`.
2. Review `bundle.md` and captured text.
3. Promote only concrete, cited opportunities into deep source adapter/manual staging.
4. Keep public listings as `PUBLIC_SEARCH_RESULT` / `DETAIL_PAGE_CAPTURED`, not supplier quote proof.
