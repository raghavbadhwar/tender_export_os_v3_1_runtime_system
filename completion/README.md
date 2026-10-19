# Completion Packet

This directory turns the remaining production work into small, deterministic tasks that a tool-using coding model can execute safely. It does not claim that the project is production-ready.

## Executor protocol

1. Run `python3 completion/validate.py --next`.
2. If no task is `ready`, stop and report the blocker. Do not promote a task by guessing.
3. Read only the selected task's `context_files`, plus repository instructions they reference.
4. Change only `allowed_paths`, stay within `max_changed_files`, and execute one task per run.
5. Never commit, push, deploy, publish, send, purchase, use DSC, or use credentials from this packet.
6. Run every command in `checks`. Retry a failing command at most twice, fixing the root cause only inside scope.
7. On success, write the named evidence receipt, set that task to `done`, promote at most one dependency-unblocked task to `ready`, and rerun the validator.
8. On missing credentials, unavailable services, ambiguous requirements, or a stop condition, set the task to `blocked` with a factual blocker and stop.

## Evidence receipt

Each completed task writes JSON at its `evidence_receipt` path:

```json
{
  "schema_version": "completion_evidence.v1",
  "task_id": "TEOS-01",
  "result": "pass",
  "base_commit": "git-sha-before-task",
  "files_changed": ["relative/path"],
  "checks": [{"command": "exact command", "exit_code": 0, "summary": "short factual result"}],
  "limitations": [],
  "external_actions_executed": false
}
```

The validator rejects `done` without this receipt, zero-exit checks, and path/file-count compliance.

## Small-model prompt

```text
Read AGENTS.md, completion/README.md, and completion/plan.json. Run python3 completion/validate.py --next. Execute exactly the returned task and no other task. Do not edit outside allowed_paths. Do not commit, push, deploy, publish, send, submit, pay, use DSC, or use live credentials. Run every listed check. If all checks pass, write the evidence receipt, mark only this task done, promote at most one newly unblocked task to ready, and rerun the validator. Otherwise record the blocker and stop.
```

