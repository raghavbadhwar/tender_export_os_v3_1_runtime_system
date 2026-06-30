# Approval Card Prompt — Hermes

## Instructions for Generating Approval Cards in Hermes

When I say `show approvals` or when viewing a specific approval card, use this to format the output.

---

## Mobile Approval Card Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 APPROVAL REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Case:        [case_id]
 Workflow:    [GOV / EXPORT]
 Action:      [proposed_action in plain English]
 Object:      [what will happen externally]

 Amount:      [₹ or $ amount, or N/A]
 Deadline:    [date / [N days remaining]]

 ─────────────────────────────────────────
 BENEFIT
 [1–2 lines. Specific and quantified where possible.]

 RISK IF WE PROCEED
 [1–2 lines. Realistic worst case.]

 RISK IF WE DON'T
 [1 line. What we lose by not acting.]

 RECOVERY PATH
 [1 line. What can be undone if this goes wrong.]
 ─────────────────────────────────────────

 Confidence:  [N]/100
 Missing:     [explicit list or "None"]

 Documents:
 • [document 1]
 • [document 2]

 ─────────────────────────────────────────
 DECIDE:
   A → Approve
   R → Reject
   C → Ask for changes

 Say: approve case [case_id]
      reject case [case_id]
      ask changes [case_id]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Sample Approval Card

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 APPROVAL REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Case:        EXP-20260630-002
 Workflow:    EXPORT
 Action:      Send export quotation to UK buyer
 Object:      Gulf Naturals Trading LLC — Brass Handicraft 200pcs

 Amount:      $680 CIF London
 Deadline:    2026-07-01 [1 day remaining for quote validity]

 ─────────────────────────────────────────
 BENEFIT
 First UK buyer relationship. $680 order with 22% margin (~$150 net).
 Low risk — buyer verified, LC payment preferred.

 RISK IF WE PROCEED
 Buyer counters on price. Supply delay from Jaipur artisan.

 RISK IF WE DON'T
 Lose a verified UK buyer we spent 3 days qualifying.

 RECOVERY PATH
 If buyer not happy — counter-offer at FOB $620. Supplier backup identified.
 ─────────────────────────────────────────

 Confidence:  82/100
 Missing:     Phytosanitary cert not needed. COO from FIEO — 1 day process.

 Documents:
 • EXP-20260630-002 export quote pack
 • Compliance draft — ITC-HS 8306.29 candidate (expert to confirm)
 • Supplier quote from Artisan Craft India — ₹380/pc confirmed

 ─────────────────────────────────────────
 DECIDE:
   A → Approve
   R → Reject
   C → Ask for changes

 Say: approve case EXP-20260630-002
      reject case EXP-20260630-002
      ask changes EXP-20260630-002
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
