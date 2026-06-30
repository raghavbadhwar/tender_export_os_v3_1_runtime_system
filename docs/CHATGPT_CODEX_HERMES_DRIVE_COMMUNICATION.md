# ChatGPT, Codex, and Hermes Drive Communication Contract

## Decision

Google Drive is the communication bus between ChatGPT and Codex/Hermes.

`data/events.jsonl` remains the local canonical state stream. Drive is the shared packet exchange, artifact vault, and projection layer. ChatGPT must never directly mutate the operating registers.

## Drive Root

```text
Tender Export OS - Knowledge Bus/
```

## Stable Context Folder

```text
00_Project_Context/
|-- 01_Instructions/
|-- 02_State_Snapshots/
`-- 03_Context_Receipts/
```

Folder URL:
`https://drive.google.com/drive/folders/1jAxbgUzSWzBe9OWlBOPlE8Mh2w73sfiV`

Use this folder for durable project context that should remain visible across Hermes, Codex, and ChatGPT work. Do not use it for raw databases, secrets, credential files, DSC files, bank details, or unreviewed private supplier claims.

## Communication Lanes

```text
08_ChatGPT_Bridge/
|-- 01_To_ChatGPT/
|   |-- <timestamp>_<topic>/
|   |   |-- chatgpt_snapshot.md
|   |   |-- CHATGPT_BOARDROOM.md
|   |   |-- project_instructions.md
|   |   `-- packet_manifest.json
|-- 02_From_ChatGPT/
|   `-- <ChatGPT research returns uploaded here>
`-- 03_Reviewed_For_Codex_Hermes/
    `-- <Hermes/Codex-reviewed tasks, plans, or accepted findings>
```

## Direction A - Codex/Hermes to ChatGPT

Use:

```bash
python3 scripts/prepare_chatgpt_drive_packet.py
python3 scripts/sync_to_drive.py --group 08_ChatGPT_Bridge
```

The packet contains bounded context only:

- active case summary
- pending approval summary
- quote-proof gaps
- source/plugin health
- recommended owner action
- boardroom instructions
- packet manifest and boundaries

Do not send raw operational databases, credentials, DSC files, cookies, bank details, or unreviewed private supplier claims.

## Direction B - ChatGPT to Codex/Hermes

ChatGPT returns research or strategy into:

```text
08_ChatGPT_Bridge/02_From_ChatGPT/
```

After importing or placing a return locally, stage it with:

```bash
python3 scripts/stage_chatgpt_return.py --input <return-file>
```

The staging step creates a review plan and does not mutate state.

## Review Rule

ChatGPT output is advisory until reviewed. Hermes/Codex may convert accepted findings into:

- a Hermes task
- a Codex artifact request
- a case note
- a new event in `data/events.jsonl`
- an owner approval card

But ChatGPT output alone must not:

- approve external action
- submit a tender
- send a buyer/supplier message
- confirm HSN/ITC-HS
- claim origin
- commit price
- commit delivery
- overwrite registers

## Local Scripts

- `scripts/prepare_chatgpt_drive_packet.py` prepares outbound packets.
- `scripts/stage_chatgpt_return.py` stages inbound returns.
- `scripts/sync_to_drive.py` dry-runs or uploads Drive artifacts.
- `scripts/import_from_drive.py` dry-runs or imports Drive artifacts.
- `scripts/validate_register_schemas.py` validates local state after any accepted import.

## Acceptance Check

```bash
python3 scripts/system_health_check.py --runtime
```
