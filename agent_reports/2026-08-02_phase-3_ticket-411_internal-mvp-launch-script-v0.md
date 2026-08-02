---
template_id: build_report
template_version: 1.0.0
status: current
---

# Build Report: Phase 3 / ticket-411 / internal MVP launch script v0

## 1. Summary

Added a one-command Windows launcher that forces mock-only research settings, runs the
researcher product proof on gitignored scratch paths, fails closed unless
`product_verdict` is `GO`, prints the canonical research prompt, and starts the static
Atlas preview on `127.0.0.1:3000`. README now documents the launcher with a process-scoped
PowerShell execution-policy override for machines where local scripts are restricted.

## 2. Ticket

- Ticket ID: ticket-411
- Ticket title: Internal MVP one-command launch script v0
- Branch: `phase-3/ticket-411-internal-mvp-launch-script-v0`
- Phase: 3
- Agent/model: Codex (GPT-5)
- Date: 2026-08-02
- Main tip before branch: `58b6d5e`

## 3. Scope

### In Scope

- Windows PowerShell launcher.
- Mock-only product-proof and `GO` gate.
- Local Atlas preview startup and README instructions.
- Ticket/report/queue bookkeeping and the next proposed ticket.

### Out of Scope / Non-Goals

- Live OpenAI, OpenAlex, or Ollama.
- Private FastAPI or port 8000.
- Topic/question input UI.
- Engine or safety-gate changes.
- Pre-existing local-source research changes already present in the working tree.

## 4. Changed Files

| File | Change Summary |
|---|---|
| `scripts/launch_internal_mvp.ps1` | Mock-only proof, verdict gate, dependency check, and localhost Atlas dev server |
| `README.md` | One-command launch section and restricted-policy-safe invocation |
| `tickets/ticket-411.json` | Status `done` |
| `tickets/ticket-412.json` | Proposed automated launcher contract test |
| `tickets/TICKET_QUEUE.md` | Ticket-411 completion, ticket-412 active proposal, and queue notes |
| `agent_reports/2026-08-02_phase-3_ticket-411_internal-mvp-launch-script-v0.md` | This report |

## 5. Implementation Notes

- The launcher sets `RGE_LLM_MODE=mock` and `RGE_ALLOW_LIVE_LLM=0` before proof execution.
- It reads the generated JSON artifact rather than trusting command exit alone; `PARTIAL`
  therefore cannot start the preview.
- Next.js binds explicitly to `127.0.0.1:3000`. Port 8000 is never started.
- `npm install` runs only when `apps/public-site/node_modules/` is absent.
- Existing unrelated working-tree changes were preserved and excluded from ticket staging.

## 6. Acceptance Criteria Status

| Acceptance Criteria | Status | Notes |
|---|---|---|
| Sets mock mode and disables live LLM | PASS | Confirmed statically and during launch |
| Runs product proof on scratch paths and prints verdict | PASS | `product_verdict: GO` |
| Prints default prompt and starts localhost:3000 preview | PASS | Next.js reported ready on `127.0.0.1:3000` |
| Prints `/atlas-preview` URL and does not start port 8000 | PASS | URL printed; no port-8000 command or listener |
| README points to one-command launch | PASS | Process-scoped execution-policy command documented |

## 7. Commands Run

| Command | Result | Notes |
|---|---|---|
| PowerShell AST parse of `scripts/launch_internal_mvp.ps1` | PASS | No syntax errors |
| `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\launch_internal_mvp.ps1` | PASS | Proof GO; Next.js ready; validation wrapper timed out intentionally to stop foreground dev server |
| `.venv-ci-test\Scripts\python.exe -m pytest tests\golden -q` | PASS | 165 passed |
| `.venv-ci-test\Scripts\python.exe -m pytest -q` | PASS | 1411 passed, 50 deselected |
| `python -m rge.modules.safety_auditor --audit full` | PASS | No blocked reasons |
| `npm.cmd run build` | PASS | Static `/atlas-preview` exported |
| `git push origin main` | PASS | Fast-forwarded `origin/main` from `58b6d5e` to `e51b105` |

## 8. Test Results

### Passing

- Launcher product proof: `GO`; 3 sources, 2 claims, 2 evidence rows.
- Product-proof safety snapshot: pass; no live OpenAI use.
- Golden: 165 passed.
- Full pytest: 1411 passed, 50 deselected.
- Public-site build: pass.

### Failing

- None.

### Not Available Yet

- None.

## 9. Safety Audit Status

- Required: yes (fixed shell/npm launcher surface)
- Status: pass
- Notes: Full audit found no public write, ingestion, agent-execution, export, route, or
  secret violations.

## 10. Spec Deviations

None. The README uses a process-scoped `-ExecutionPolicy Bypass` invocation because the
host policy blocks direct `.ps1` execution; it does not change user or machine policy.

## 11. Known Risks / Gaps

- Launcher guarantees are manually proven but not yet automated; ticket-412 addresses this.
- Full-tree `git diff --check` also reports a pre-existing blank line at EOF in the
  user-modified `scripts/run_full_atlas_refresh_checklist.py`; ticket-scoped files are clean.
- Launcher contract coverage remains proposed as ticket-412.

## 12. Rollback Plan

Delete `scripts/launch_internal_mvp.ps1` and revert only the README one-command section,
queue bookkeeping, and report/ticket files from this ticket.

## 13. Recommended Next Ticket

```json
{
  "id": "ticket-412",
  "title": "Internal MVP launcher contract tests v0",
  "problem": "The launcher boundary is manually proven but lacks deterministic regression coverage.",
  "expected_files": ["tests/unit/test_internal_mvp_launcher.py"],
  "risk_level": "low"
}
```

## 14. Suggested Next Prompt

```txt
Implement ticket-412 on its own branch. Add deterministic tests for the launcher contract,
run the ticket test plan, full safety audit, and write the next smallest ticket.
```

## Merge to Main

Merge commit: `5b2654e9aad28e31d233f96197542ef02641e69e`.

Post-merge report commit: `320b592`.

Push status: **COMPLETED** — `origin/main` was fast-forwarded from `58b6d5e` to
`e51b105` on 2026-08-02 after explicit user authorization.
