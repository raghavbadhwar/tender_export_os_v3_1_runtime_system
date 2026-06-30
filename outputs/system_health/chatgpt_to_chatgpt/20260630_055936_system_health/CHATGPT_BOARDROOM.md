# ChatGPT Boardroom

## Role
ChatGPT Project is the deep research and strategy boardroom. It is not the operational database, not the bid sender, and not the final compliance authority.

## Use ChatGPT For
- source-cited public web research
- market and category analysis
- export country research
- competitor/operator model research
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
- bid submission
- direct supplier or buyer sends
- storing all memory
- final compliance authority

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

## Sources
- User upgrade brief: `/Users/raghav/.codex/attachments/50962de5-cb39-48a4-8d6e-31bce3df71ac/pasted-text.txt`
