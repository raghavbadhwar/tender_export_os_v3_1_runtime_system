# ChatGPT Boardroom

## Role
ChatGPT Project is the deep research and strategy boardroom. It is not the operational database, not the bid sender, and not the final compliance authority.

The executable split is defined in:
- `docs/HYBRID_RESEARCH_AND_CAPTURE_MODEL.md`
- `config/research_capture_routing.yaml`
- `docs/DEEP_RESEARCH_TO_REPO_STAGING.md`
- `config/schemas/deep_research_lead_schema.yaml`

Operating summary:
- Deep Research discovers.
- Python/Playwright captures and proves.
- The repo remembers and audits.
- Hermes routes and enforces approvals.
- The owner decides external, money, legal, DSC, price, classification, origin, and delivery commitments.

## Use ChatGPT For
- source-cited public web research
- market and category analysis
- export country research
- competitor/operator model research
- low-competition category and source thesis discovery
- repeat-buyer and buyer-pattern discovery across unknown public sources
- industry report synthesis
- strategic weekly review
- dashboard interpretation
- ranking categories
- improving prompts and rules
- reviewing opportunities at business-model level

## Do Not Use ChatGPT For
- raw operational database storage
- local file runtime
- daily parsing
- source-specific repeatable capture
- document downloading or BOQ/PDF parsing
- event-ledger mutation
- approval receipt creation
- bid submission
- direct supplier or buyer sends
- storing all memory
- final compliance authority
- final price, HSN/ITC-HS, origin, delivery, legal, or tax claims

ChatGPT Scheduled Deep Research may flag a lead, but it cannot create a bid-ready case. `PUBLIC_LISTING_ONLY` is always a lead. A case candidate requires operational evidence such as downloaded documents, manually uploaded evidence, source detail capture, a structured evidence bundle, or owner-approved manual source check.

## Drive Communication Bridge
ChatGPT communicates with Codex/Hermes only through the Drive bridge:

```text
Tender Export OS - Knowledge Bus/08_ChatGPT_Bridge/
|-- 01_To_ChatGPT/
|-- 02_From_ChatGPT/
`-- 03_Reviewed_For_Codex_Hermes/
```

Outbound packets are prepared with:

```bash
python3 scripts/prepare_chatgpt_drive_packet.py
```

Each packet must summarize:
- active GOV cases
- active EXPORT cases
- top opportunities
- pending approvals
- supplier issues
- source health
- plugin health
- main risks
- recommended owner action

Generate it with:

```bash
python3 scripts/prepare_chatgpt_drive_packet.py
```

## Return Path
ChatGPT research outputs should be saved back into `08_ChatGPT_Bridge/02_From_ChatGPT/`.

Codex/Hermes stages returns with:

```bash
python3 scripts/stage_chatgpt_return.py --input <return-file>
```

Staged returns are advisory until reviewed. They do not mutate `data/events.jsonl` or CSV registers by themselves.

Scheduled Deep Research lead reports use the narrower staging contract:

```bash
python3 scripts/stage_deep_research_leads.py --input <saved-deep-research-report-or-json> --dry-run
python3 scripts/stage_deep_research_leads.py --input <saved-deep-research-report-or-json> --stage
```

This helper is not a web-research scraper. It validates manually saved Deep Research lead data, dedupes against existing cases and staged leads, writes `outputs/deep_research_staging/`, and only appends `deep_research.leads_staged` when `--stage` is explicitly used. It does not mutate `data/master_cases.csv` by default.

## Low-Competition Orders
ChatGPT Scheduled Deep Research finds the low-competition thesis and source/category signals. Python/Playwright then proves, tracks, dedupes, scores, and stores shortlisted evidence from known sources.

Correct low-competition flow:
1. Deep Research reports a cited public lead, retender signal, buyer pattern, or category thesis.
2. Hermes/owner chooses which leads are worth staging.
3. `stage_deep_research_leads.py` validates and stages the saved leads.
4. Radar/source runtime checks known sources and captures evidence.
5. Fast Kill or Deep Read starts only when evidence supports it.

## Sources
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
