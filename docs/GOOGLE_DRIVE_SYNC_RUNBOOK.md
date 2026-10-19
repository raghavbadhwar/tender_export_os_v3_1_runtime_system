# Google Drive Sync Runbook

Status: dry-run manifest support implemented. One non-sensitive Google Drive upload tested successfully after owner approval.

Latest successful receipt: `receipts/drive_sync/SYSTEM-90PLUS-DELIVERY-TEST_20260630124313_google_drive_sync.json`.

Planned folders:
- Project Context
- Cases
- Approvals
- Evidence
- Briefs
- Receipts
- Dashboards

Use `scripts/sync_drive_manifest.py --dry-run --case-id <case_id>` to build local checksummed manifest rows without uploading. Do not print credential files, tokens, cookies, or secrets.

Current tested external path: `Tender Export OS - Knowledge Bus/90_Plus_External_Tests/`.

Current project-context path: `Tender Export OS - Knowledge Bus/00_Project_Context/`

Current project-context URL: `https://drive.google.com/drive/folders/1jAxbgUzSWzBe9OWlBOPlE8Mh2w73sfiV`

Use `00_Project_Context/01_Instructions` for durable instructions and communication contracts, `00_Project_Context/02_State_Snapshots` for bounded state snapshots, and `00_Project_Context/03_Context_Receipts` for folder/sync receipts. Real file upload still requires explicit execute mode and connector authentication.
