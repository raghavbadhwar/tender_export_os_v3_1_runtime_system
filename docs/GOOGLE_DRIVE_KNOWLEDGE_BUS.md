# Google Drive Knowledge Bus

## Decision
Google Drive remains the shared knowledge bus, communication layer, and artifact vault.

`data/events.jsonl` remains the local canonical state stream. Drive carries projections, packets, returns, receipts, and artifacts between ChatGPT, Codex, and Hermes.

## Folder Structure
```text
Tender Export OS - Knowledge Bus/
|-- 00_Project_Context/
|   |-- 01_Instructions/
|   |-- 02_State_Snapshots/
|   `-- 03_Context_Receipts/
|-- 00_Control_Center/
|   |-- master_cases.xlsx
|   |-- supplier_master.xlsx
|   |-- approval_queue.xlsx
|   |-- source_health.xlsx
|   |-- plugin_health.xlsx
|   |-- quote_master.xlsx
|   `-- agent_run_log.xlsx
|-- 01_Daily_Briefs/
|   `-- YYYY-MM-DD_daily_brief.html
|-- 02_Case_Reports/
|-- 03_Bid_Packs/
|-- 04_Export_Quote_Packs/
|-- 05_Supplier_Proof/
|-- 06_Receipts/
|   |-- approvals/
|   |-- owner_decisions/
|   |-- supplier_quotes/
|   |-- submissions/
|   `-- plugin_runs/
|-- 07_Config_Snapshots/
|-- 08_ChatGPT_Bridge/
|   |-- 01_To_ChatGPT/
|   |-- 02_From_ChatGPT/
|   `-- 03_Reviewed_For_Codex_Hermes/
|-- 09_Plugin_Produced_Artifacts/
|   |-- Excel_Models/
|   |-- PDF_Packs/
|   |-- DOCX_Proposals/
|   |-- PPTX_Decks/
|   |-- Invoices/
|   |-- Email_Sequences/
|   `-- Dashboards/
`-- 10_Archive/
```

Current project-context folder:
`https://drive.google.com/drive/folders/1jAxbgUzSWzBe9OWlBOPlE8Mh2w73sfiV`

`00_Project_Context` is the durable instruction and shared-context vault. `08_ChatGPT_Bridge` remains the packet exchange lane for bounded ChatGPT handoffs and returns.

## Sync Rules
Sync:
- project instructions, communication contracts, and bounded state snapshots into `00_Project_Context`
- control-center CSV/XLSX registers
- daily briefs
- case reports
- bid packs
- export quote packs
- supplier proof artifacts
- approval and execution receipts
- config snapshots
- ChatGPT bridge packets and reviewed returns
- plugin-produced artifacts

Never sync:
- secrets
- cookies
- DSC files
- credentials
- raw browser cache
- private tokens
- passwords
- bank details
- unverified supplier claims as final facts

## Scripts
Use:

```bash
python3 scripts/prepare_chatgpt_drive_packet.py
python3 scripts/sync_to_drive.py --group 08_ChatGPT_Bridge
python3 scripts/import_from_drive.py --group 08_ChatGPT_Bridge
python3 scripts/stage_chatgpt_return.py --input <return-file>
```

These scripts are manifest/dry-run first. Actual Google Drive upload/download requires connector authentication and explicit owner configuration.

Communication contract: `docs/CHATGPT_CODEX_HERMES_DRIVE_COMMUNICATION.md`

## Sources
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
