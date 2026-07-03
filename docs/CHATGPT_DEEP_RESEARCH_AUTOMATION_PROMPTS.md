# ChatGPT Deep Research Automation Prompts

These prompts are for bounded ChatGPT Project and Drive handoff lanes only. They do not make ChatGPT canonical state. `data/events.jsonl` remains canonical, and repo staging must go through `scripts/stage_deep_research_leads.py`.

## Files

- `templates/chatgpt/master_drive_deep_research_return_prompt.md` — easiest single copy/paste prompt for the full Drive packet → deep research → Drive return loop.
- `templates/chatgpt/drive_handoff_prompt.md`
- `templates/chatgpt/deep_research_prompt.md`
- `templates/chatgpt/return_to_drive_prompt.md`

## Required Return Contract

Every ChatGPT research return must include:

- citations and source URLs for every factual claim
- uncertainty notes and missing information
- no external actions and no operational register mutation
- a structured JSON appendix with a top-level `leads` array compatible with `config/schemas/deep_research_lead_schema.yaml`

Use the repo staging command after saving the return locally or through the Drive bridge:

```bash
python3 scripts/stage_deep_research_leads.py --input <saved_chatgpt_return.json_or_md> --dry-run
```

## Forbidden In ChatGPT Output

ChatGPT must not ask anyone to submit, upload, send, pay, use DSC, mutate `data/*.csv`, commit final prices, final delivery terms, origin claims, HS/HTS/ITC-HS classifications, or final legal/compliance positions.
