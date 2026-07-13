# Agentic Review Enqueuer

`scripts/enqueue_agentic_reviews.py` creates durable Hermes Kanban review cards only when input packets exist.

It supports:

- morning chief operator review;
- intraday exception officer review;
- weekly learning council review.

The enqueuer does not run a model, contact anyone, submit anything, or execute external actions. It is dry-run by default. `--write` is required to call `hermes kanban create`.
