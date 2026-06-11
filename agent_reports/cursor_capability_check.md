# Cursor Capability Check

**Date:** 2026-06-11  
**Repo version:** V000 (documentation and agent-ops harness only; no implementation verified)  
**Checker:** Cursor agent (read-only inspection except this report)

---

## 1. Summary

The Research Graph Engine workspace is a clean Git repo on `main` with documentation, Cursor rules/commands, ticket queue metadata, and report templates. No Python package, tests, CLI, or `apps/public-site` exist yet, which matches the expected V000 state.

Cursor agent tooling in this session can read the workspace, run non-destructive shell commands, and write files. The repo-level harness is largely present but has **path inconsistencies** between docs/commands (`agent_reports/`, `tickets/` at repo root) and the actual folders (`docs/agent_reports/`, `docs/tickets/`).

Tooling prerequisites for future verification are partially ready: **Python 3.14.3**, **pytest 9.0.2** (`python -m pytest`), **npm 11.11.0**, **git 2.44.0**, and **gh 2.89.0** are available. Implementation commands (`research`, golden tests, public-site build) are **NOT AVAILABLE** until Phase 0 scaffold lands.

Plan Mode and background subagents are available through agent tooling. Exact Cursor UI approval toggles for terminal/Git were **not verified** from this workspace.

---

## 2. Workspace Visibility

| Check | Result |
|---|---|
| Workspace root | `C:\Users\guestt\OneDrive\Desktop\Kooya\rage` |
| `AGENTS.md` readable | **Yes** — present at repo root |
| Agent specs under `docs/agents/` | **Yes** — 12 spec files + templates |
| `.cursor/rules/` | **Yes** — `rge-core.mdc` |
| `.cursor/commands/` | **Yes** — 4 RGE commands |
| Implementation code (`rge/`, `tests/`, `apps/`) | **No** — not present (expected for V000) |
| Git repository | **Yes** — remote `origin` → `https://github.com/Hlax/rage.git` |

### Answers (workspace-related)

**2. Is `AGENTS.md` visible and usable as repo-level guidance?**  
**Yes.** It is at the repo root, readable, and also injected as an always-applied workspace rule in this Cursor session.

**8. What is the current working directory?**  
`C:\Users\guestt\OneDrive\Desktop\Kooya\rage` (verified via shell `Get-Location` after `Set-Location`).

---

## 3. Cursor Rules and Commands

### Loaded or discoverable rules

| Source | Location | Scope | Verified |
|---|---|---|---|
| RGE core rule | `.cursor/rules/rge-core.mdc` | `alwaysApply: true`, globs `**/*` | **Yes** |
| Repo operating guide | `AGENTS.md` | Always-applied workspace rule in session | **Yes** |
| User rules | Cursor user settings (not in repo) | Session-level (git safety, PR workflow, communication, code principles) | **Yes** (in session) |
| Agent skills | `~/.cursor/skills-cursor/`, `~/.agents/skills/` | Available on demand | **Yes** (listed in session) |

No other `.cursor/rules/*.mdc` files were found in the repo.

**1. Which Cursor rules are loaded or discoverable?**  
- **Repo:** `.cursor/rules/rge-core.mdc` (always apply).  
- **Repo:** `AGENTS.md` (always-applied workspace guidance).  
- **Session:** Cursor user rules and agent skills (outside repo; loaded by Cursor).

### Commands

| Command file | Purpose |
|---|---|
| `.cursor/commands/rge-phase0-scaffold.md` | Phase 0 / 0.5 scaffold instructions |
| `.cursor/commands/rge-verify.md` | Phase-appropriate verification |
| `.cursor/commands/rge-handoff.md` | Handoff report generation |
| `.cursor/commands/rge-next-ticket.md` | Next-ticket proposal |

**3. Are `.cursor/commands` available from this workspace?**  
**Yes.** Four markdown command files exist under `.cursor/commands/`. They are discoverable as Cursor workspace commands (typically invoked as `/rge-*` slash commands in the Cursor command UI). Actual UI registration was not re-tested interactively in this session.

---

## 4. Agent/Plan/Multitask Capabilities

**4. Is Plan Mode available?**  
**Yes (agent tooling verified).** The agent has a `SwitchMode` tool supporting `plan` and `agent` modes. Switching requires user consent per tool description.

**5. Is `/multitask` available, and if so, how does it isolate work?**  
**Partially verified.**  
- The agent `Task` tool supports `run_in_background: true` and documents **Multitask Mode** (background subagents notify on completion).  
- The `best-of-n-runner` subagent type runs work in **isolated git worktrees**, each with its own branch and working directory.  
- Whether the exact **`/multitask` slash command** appears in the Cursor UI for this user: **UNKNOWN / NOT VERIFIED** (no interactive UI inspection performed).

**6. Are background/cloud agents available?**  
**Partially verified.**  
- **Background subagents:** Yes via `Task` tool with `run_in_background: true` (types include `generalPurpose`, `explore`, `shell`, `bugbot`, `security-review`, `best-of-n-runner`, etc.).  
- **Cloud agents:** Referenced in Cursor SDK/docs but **not verified** as enabled or configured for this user/workspace.

---

## 5. Terminal and Git Capabilities

### Terminal

| Item | Value |
|---|---|
| Shell (user info) | **PowerShell** |
| OS | Windows 10.0.26200 |
| `ComSpec` | Present (Windows cmd path; agent shell runs PowerShell per user_info) |
| Command chaining | Use `;` in PowerShell — `&&` failed in this session |

**7. What terminal shell will commands run in?**  
**PowerShell** (per session user_info; verified by successful PowerShell-style commands).

### Git state

| Item | Value |
|---|---|
| Branch | `main` |
| Tracking | Up to date with `origin/main` |
| Working tree | **Clean** — nothing to commit |
| Remote | `origin` → `https://github.com/Hlax/rage.git` |

**9. What is the current Git branch?**  
`main`

**10. Is the working tree clean?**  
**Yes.**

### File, directory, Git, and PR capabilities

| Capability | Status | Notes |
|---|---|---|
| Create local files | **Yes** | Write tool available; this report created successfully |
| Create directories | **Yes** | Implicit when writing nested paths (e.g. `agent_reports/`) |
| Create Git branches | **Yes (capability)** | `git` available; not exercised in this check per instructions |
| Push to remote | **Yes (capability)** | Remote configured; would require network + user approval |
| Open PRs | **Yes (capability)** | `gh` 2.89.0 installed; not exercised in this check |

**11–15.** See table above. No branch creation, push, or PR was performed during this inspection.

### Approval settings

**16. What approval settings apply to terminal commands?**  
**UNKNOWN / NOT VERIFIED** for exact Cursor UI settings (auto-run vs ask-every-time). Observed behavior in this session:
- Non-destructive read-only commands (`git status`, `python --version`) ran without blocking.
- Tooling supports **Smart Mode approval cards** for blocked/retry flows (`request_smart_mode_approval` on Shell/MCP tools).
- Destructive or repo-modifying commands were intentionally not run.

**17. What approval settings apply to Git commands?**  
**UNKNOWN / NOT VERIFIED** for Cursor-specific Git approval UI. Agent user rules additionally constrain the agent: no destructive git without explicit user request, no force push to main, no config changes, commits only when asked.

---

## 6. Test and Build Readiness

### Runtime tools

| Tool | Version / status |
|---|---|
| Python | 3.14.3 |
| pytest | 9.0.2 (`python -m pytest --version`) |
| npm | 11.11.0 |
| git | 2.44.0.windows.1 |
| gh | 2.89.0 |

### Implementation artifacts (expected missing at V000)

| Artifact | Status |
|---|---|
| `pyproject.toml` / package layout | **Missing** |
| `tests/` / `tests/golden/` | **Missing** |
| `research` CLI | **Missing** |
| `apps/public-site/` | **Missing** |
| `rge/` Python package | **Missing** |

**18. Can you run Python commands?**  
**Yes.** `python --version` succeeded.

**19. Can you run `pytest` if/when tests exist?**  
**Yes (runner available).** `pytest` 9.0.2 is installed. No tests exist yet; running `pytest` today would collect zero tests or error on missing config — not run to avoid noise.

**20. Can you run npm commands if/when `apps/public-site` exists?**  
**Yes (runner available).** `npm` 11.11.0 is installed. `apps/public-site` does not exist yet.

Default verification commands from `AGENTS.md` / rules:

| Command | Current status |
|---|---|
| `pytest` | Runner OK; **no tests** |
| `pytest tests/golden` | **NOT AVAILABLE** |
| `research --help` | **NOT AVAILABLE** |
| `research run ... --fixture-mode` | **NOT AVAILABLE** |
| `research export-public --limit 100` | **NOT AVAILABLE** |
| `python -m rge.modules.safety_auditor --audit full` | **NOT AVAILABLE** |
| `cd apps/public-site && npm run build` | **NOT AVAILABLE** (use `;` on PowerShell when implemented) |

---

## 7. Agent-Ops Harness Check

### Present

| Item | Path | Status |
|---|---|---|
| Root operating guide | `AGENTS.md` | OK |
| Canonical specs | `docs/agents/01_…` through `11_…`, `00_GOLDEN_TESTS.md`, etc. | OK |
| Build loop / safety / MVP specs | `docs/agents/04_…`, `07_…`, `10_…`, `11_…` | OK |
| Report templates | `docs/agents/templates/BUILD_REPORT_TEMPLATE.md`, `NEXT_AGENT_HANDOFF_TEMPLATE.md` | OK |
| Template registry | `docs/agents/templates/TEMPLATE_REGISTRY.md` | OK |
| Template archive dir | `docs/agents/templates/archive/` | Exists (empty) |
| Ticket queue doc | `docs/tickets/TICKET_QUEUE.md` | OK |
| Report folder README | `docs/agent_reports/README.md` | OK |
| Cursor rule | `.cursor/rules/rge-core.mdc` | OK |
| Cursor commands | `.cursor/commands/rge-*.md` (×4) | OK |

### Missing or inconsistent

| Issue | Detail |
|---|---|
| **Path mismatch: agent reports** | Docs/rules/commands reference `agent_reports/` at repo root. Actual folder is `docs/agent_reports/` (only `README.md` today). Root `agent_reports/` did not exist before this check file. |
| **Path mismatch: ticket queue** | `rge-next-ticket.md` references `tickets/` at root. Actual queue lives at `docs/tickets/TICKET_QUEUE.md`. Root `tickets/` does not exist. |
| **No ticket JSON files** | Queue lists `ticket-001` as `ready` but no `tickets/*.json` or `docs/tickets/*.json` scaffold files yet. |
| **Dual meaning of `tickets/`** | MVP specs also use `tickets/improvement_ticket_latest.json` as a **runtime artifact** path (post-implementation), separate from the agent-ops ticket queue — potential confusion until documented in scaffold. |
| **Minimal README** | Root `README.md` is only `# rage`. |

**21. Are there any missing folders or files from the agent-ops harness?**  
Most harness docs exist. Gaps: **root vs `docs/` path alignment**, **no ticket JSON files**, empty template archive (acceptable at v1.0.0). No implementation folders (expected).

**22. Are there any conflicts between the current docs/rules/commands?**  
**Yes — minor but actionable path conflicts:**

1. **`agent_reports/` location:** `AGENTS.md`, `rge-core.mdc`, `rge-handoff.md`, `rge-verify.md`, `rge-phase0-scaffold.md`, and `11_AGENT_OPERATING_PROTOCOL.md` say `agent_reports/` at root; physical folder and README are under `docs/agent_reports/`.
2. **`tickets/` location:** `rge-next-ticket.md` says read/write `tickets/` at root; queue is at `docs/tickets/TICKET_QUEUE.md`.
3. **`docs/agent_reports/README.md`** aligns with `docs/agents/templates/` but contradicts root-level paths in `AGENTS.md` and `.cursor/rules`.
4. No substantive conflict on safety rules, mock LLM mode, or one-ticket-per-branch policy across specs.

Recommend resolving paths in a **documentation-only ticket** before Phase 0 implementation so reports and ticket JSON land in one canonical place.

---

## 8. Safety Concerns

**23. Are there any safety concerns before Phase 0 implementation?**

| Concern | Severity | Notes |
|---|---|---|
| Path ambiguity for reports/tickets | Medium | Agents may write to wrong folders; breaks queue “done requires report” rule. |
| Python 3.14.3 | Low–Medium | Very new interpreter; pin supported version in scaffold (`pyproject.toml`) and CI early. |
| PowerShell vs bash examples | Low | Docs use `&&`; use `;` or separate commands on Windows. |
| Clean `main` with no branch protection verified | Low | Phase 0 should use `phase-0/ticket-001-…` branch per specs; not verified on GitHub. |
| No `.env.example` yet | Expected | Must be added in scaffold without secrets. |
| Safety model requirements | High (design) | Specs correctly require: no public write/ingestion/agent routes, no model-controlled shell/Git, mock LLM in golden tests, staging before accepted DB writes. These are **design constraints for implementation**, not current repo vulnerabilities. |
| Untrusted source handling | High (design) | Prompt-injection fixtures and deterministic safety auditor specified but not implemented yet. |

No implementation code means no runtime attack surface yet. Primary pre-Phase-0 risk is **process drift** (wrong paths, skipping mock mode, claiming success without tests).

---

## 9. Recommended Settings Before Implementation

### Documentation / harness (before code)

1. **Pick one canonical path** for agent reports and ticket JSON (`agent_reports/` vs `docs/agent_reports/`, `tickets/` vs `docs/tickets/`) and update all references in one docs-only change.
2. **Add `ticket-001` JSON** under the chosen tickets path matching `TICKET_QUEUE.md`.
3. **Confirm branch workflow:** create `phase-0/ticket-001-repo-scaffold-model-runtime` before scaffold (do not implement on `main`).

### Cursor / agent session

| Setting | Recommendation |
|---|---|
| **Planning pass model** | **Claude Opus 4.x (thinking/high)** or **Claude Sonnet 4.x (thinking)** — strong spec synthesis, ticket breakdown, risk identification; planning agent should not code unless asked. |
| **Implementation pass model** | **Composer 2.5** or **GPT-5.3 Codex** — fast multi-file scaffold, CLI/package layout, test stubs. |
| **Mode** | Plan Mode for ticket-001 scope confirmation; Agent Mode for scaffold. |
| **Rules** | Keep `rge-core.mdc` alwaysApply; ensure `AGENTS.md` stays synced with path fixes. |
| **Verification** | Use `/rge-verify` after scaffold; require mock LLM mode in golden tests. |
| **Terminal approval** | UNKNOWN — recommend **ask before run** for git push, npm install, and any command touching remotes until Phase 0 is stable. |
| **Git** | One ticket per branch; human checkpoint before merging phase branch. |

**24. Model for Phase 0/0.5 planning pass:** Claude Opus or Sonnet (thinking) for reading specs, confirming ticket-001 scope, path normalization, and acceptance criteria.

**25. Model for Phase 0/0.5 implementation pass:** Composer 2.5 or GPT-5.3 Codex for package skeleton, CLI stub, LLM adapter stubs, fixtures, and placeholder tests.

---

## 10. Recommended Next Step

1. **Resolve report/ticket path convention** (docs-only, smallest ticket or human decision).  
2. **Create branch** `phase-0/ticket-001-repo-scaffold-model-runtime`.  
3. **Run `/rge-phase0-scaffold`** (or equivalent prompt) scoped strictly to ticket-001.  
4. **Do not** implement claim extraction, LangGraph orchestration, live crawling, or public write routes.

Active ticket per queue: **`ticket-001`** — “Scaffold repo and model runtime adapter” (`ready`).

---

## 11. Suggested Next Prompt

```text
Read AGENTS.md, docs/agents/03_MODEL_RUNTIME_SPEC.md, docs/agents/04_CURSOR_BUILD_LOOP.md, docs/agents/07_MVP_ACCEPTANCE_TESTS.md, docs/agents/10_SAFETY_MODEL.md, and docs/tickets/TICKET_QUEUE.md.

Create branch phase-0/ticket-001-repo-scaffold-model-runtime.

Implement only ticket-001 Phase 0 / 0.5 scaffold per .cursor/commands/rge-phase0-scaffold.md:
- Python package skeleton, CLI stub, SQLite schema placeholder, module stubs, rge/llm/ adapter stubs, mock LLM mode, .env.example, fixture dirs, public-site placeholder, golden test placeholders.

Use mock LLM mode for all golden tests. No public write routes. No model direct DB writes.

Before claiming success, run pytest, research --help, and cd apps/public-site; npm run build (report NOT AVAILABLE for anything missing).

Write agent report using docs/agents/templates/BUILD_REPORT_TEMPLATE.md to the canonical agent_reports path we adopt.
```

---

## Appendix: Question Index

| # | Question | Short answer |
|---|---|---|
| 1 | Cursor rules loaded/discoverable? | `rge-core.mdc`, `AGENTS.md`, user rules, skills |
| 2 | AGENTS.md usable? | Yes |
| 3 | `.cursor/commands` available? | Yes (4 files) |
| 4 | Plan Mode? | Yes (SwitchMode tool) |
| 5 | `/multitask`? | Partial — Task/background/worktree isolation verified; UI slash **UNKNOWN** |
| 6 | Background/cloud agents? | Background subagents yes; cloud **UNKNOWN** |
| 7 | Terminal shell? | PowerShell |
| 8 | CWD? | `C:\Users\guestt\OneDrive\Desktop\Kooya\rage` |
| 9 | Git branch? | `main` |
| 10 | Clean working tree? | Yes |
| 11 | Create local files? | Yes |
| 12 | Create directories? | Yes |
| 13 | Create Git branches? | Yes (not exercised) |
| 14 | Push to remote? | Yes (not exercised) |
| 15 | Open PRs? | Yes (`gh` installed; not exercised) |
| 16 | Terminal approval settings? | UNKNOWN / NOT VERIFIED |
| 17 | Git approval settings? | UNKNOWN / NOT VERIFIED (+ agent git safety rules) |
| 18 | Run Python? | Yes |
| 19 | Run pytest when tests exist? | Yes |
| 20 | Run npm when public-site exists? | Yes |
| 21 | Missing harness files? | Path mismatches; no ticket JSON |
| 22 | Doc/rule/command conflicts? | Yes — report/ticket paths |
| 23 | Safety concerns pre-Phase 0? | Path drift, Python 3.14, design rules not yet enforced in code |
| 24 | Planning model? | Claude Opus/Sonnet thinking |
| 25 | Implementation model? | Composer 2.5 or GPT-5.3 Codex |

---

*End of capability check. No implementation files were modified. Only this report was created.*
