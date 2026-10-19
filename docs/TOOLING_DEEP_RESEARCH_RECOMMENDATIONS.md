# Tooling deep-research recommendations

Canonical run artifact:

```text
outputs/tooling_research/tooling_deep_research_20260703T055531Z/recommendations.md
```

Raw evidence:

```text
outputs/tooling_research/tooling_deep_research_20260703T055531Z/research_raw.json
outputs/tooling_research/tooling_deep_research_20260703T055531Z/sourcebook.md
```

## Short verdict

Do not add random MCP/plugin sprawl. The highest-value upgrades for Hermes + Tender Export OS are:

1. **Document Intelligence + Evidence Archive**: OCRmyPDF + Docling/Marker + Camelot/Tabula + ArchiveBox/WARC-style snapshots.
2. **Official procurement API adapters**: World Bank first, then UK Find a Tender, TED, SAM.gov, and OCDS normalization.
3. **Selective developer/reliability tooling**: Context7 for fresh docs during builds; Langfuse or Phoenix for agent/cron tracing after privacy boundaries.
4. **Paid search/scrape fallbacks only if needed**: Firecrawl first; then Tavily/Exa/Brave depending on whether capture or discovery recall is the bottleneck.

Recommended action: build the Document Intelligence + Evidence Archive lane before adding more paid tools.
