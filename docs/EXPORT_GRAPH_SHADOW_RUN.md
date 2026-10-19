# Export Graph Shadow Run

`scripts/shadow_run_export_case_graphs.py --write --json` builds local-only graph reports for the four current `EXP-TA-*` catalogue targets and two independently RFQ-verified export cases.

It verifies a key business boundary: catalogue fit is treated as an outreach hypothesis and is blocked from supplier, pricing, quote, and order stages until buyer-specific RFQ evidence exists. RFQ-verified cases may enter internal commercial evaluation, but every external message, quote, order, shipment, payment, classification, origin, and delivery commitment remains separately owner-gated.

The shadow runner never invokes Hermes Kanban creation, Gmail, browser automation, portals, or any external connector.
