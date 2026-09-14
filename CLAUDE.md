# CLAUDE.md — Banking Knowledge Agent

A production-style, source-backed AI support agent (RAG + MCP tools + LLM) for a
synthetic banking technology platform — built to demonstrate production AI engineering.

This file is the **sole authority** for how work is done in this repository.
It replaces `prompt.md` and `ccp.txt` (archived, unchanged, in `docs/legacy/`).

| What | Where |
|---|---|
| Permanent rules (this file) | `CLAUDE.md` |
| Project definition + Stage 1–15 detail | `docs/PROJECT_PLAN.md` |
| Current progress and recorded decisions | `docs/HANDOVER.md` |
| Architecture, reasoning, decision records | `docs/architecture-guide.html` |

---

## 1. Session start and recovery

Before doing any development work:

1. Read `docs/HANDOVER.md` — the checkpoint at the top first, then only the sections
   the current task needs.
2. Run `git status` and `git log --oneline -3`; compare with the handover.
3. Determine exactly which stage was last completed and approved.
4. Read **only the current stage's section** of `docs/PROJECT_PLAN.md` — once per
   stage, not on every turn, and never the whole file.
5. Do not repeat completed work. Do not skip unfinished work.
6. Do not start a new stage until the previous stage has been approved.

Never assume a previous Claude Code session completed work unless the actual
repository confirms it.

---

## 2. Development workflow

Work strictly **one stage at a time**.

### For every stage

1. Implement the stage.
2. Run all relevant tests; verify the implementation works.
3. Update `docs/HANDOVER.md`.
4. Report, in the format in §6.
5. **STOP.** Wait for explicit approval.

### After approval

1. Re-check the implementation and re-run the relevant tests.
2. Check `git status` and review all changes.
3. Check for secrets and unwanted files.
4. Verify there are no accidental nested project directories.
5. Update `docs/HANDOVER.md`.
6. Create a clear Git commit for the approved stage.
7. Push to the GitHub remote and verify the push succeeded.
8. Report: stage completed, commit hash, commit message, branch, push result.
9. Only then begin the next stage — and STOP again after it is implemented and tested.

### Approval cycle

```
IMPLEMENT → TEST → UPDATE HANDOVER → SHOW ME → STOP → APPROVAL
→ VERIFY → COMMIT → PUSH → VERIFY PUSH → NEXT STAGE
```

- Never skip the approval step.
- **The only thing that lifts a stop is the literal word `APPROVED`.**
- Never commit an unapproved stage.
- Never push an unapproved stage.

### Tooling

Always run checks through the project venv — never bare `python` or `pip`:

```
./.venv/Scripts/python.exe -m pytest
./.venv/Scripts/python.exe -m ruff check .
./.venv/Scripts/python.exe -m mypy
```

---

## 3. Handover file — `docs/HANDOVER.md`

The recovery point for future sessions. Never rely on conversation history as the
only record of project progress.

### Update it only when

- a stage is **completed** or **approved** (including its commit hash and push result);
- a **design decision** is made;
- a **blocker** is identified;
- the **session is ending**.

Do not update it for every small change.

### Decision rule

A decision is not recorded until it is written into `docs/HANDOVER.md`. A decision
agreed in conversation but not yet written down does not count. If a decision is made
mid-stage, before implementation begins, write it down immediately — do not wait for
stage completion.

### It must contain

| Section | Contents |
|---|---|
| Current Stage | Stage number, name, status, last completed step, next step |
| Current Work | Implemented, in progress, unfinished |
| Architecture | Current architecture, components, important design decisions |
| Files | Important files and their purpose |
| Testing | Tests run, results, commands used |
| Problems and Decisions | Known issues, blockers, assumptions, decisions |
| Git | Branch, latest commit, commit message, push status |
| Next Action | The exact next action to take |

Never put secrets, API keys, passwords or credentials in the handover file.

---

## 4. Architecture guide — `docs/architecture-guide.html`

A personal technical reference for understanding and remembering the system. It is
**not** the application's user-facing interface.

- Keep it updated whenever the architecture changes.
- **Decision rule.** A decision is not recorded until it is written into
  `docs/architecture-guide.html`. This applies to every design decision from Stage 3
  onward — including a decision presented to the user as options with a
  recommendation, and whichever option they choose. Record it **at the time it is
  made**, in the same *what / why / what was rejected* form as previous entries
  (§20 decision records), not only in the stage-end summary. Do not wait to be
  reminded.
- **Readability.** New or updated sections follow the plain-English rules in
  `docs/improve.md` ("FUTURE CHANGES"): what it does, why it exists, what problem it
  solves, how it connects to the previous and next stage. Technical term first, then a
  simple explanation. Reuse the existing `.note` style; no new CSS or classes.

---

## 5. Git rules

Never commit:

- `.env`
- API keys, passwords, tokens, credentials, generated secrets
- sensitive local databases

Always check `.gitignore`. When a new local working file appears, ignore it rather
than remembering to skip it.

The repository root is `banking-knowledge-agent`. Never create
`banking-knowledge-agent/banking-knowledge-agent`. Never create a real `.env`
containing secrets.

Before every commit, list the exact file set with `git add -An` (dry run) — `git
status` collapses untracked directories and can hide what is really being staged.

After every approved stage:

1. Verify files.
2. Verify tests.
3. Verify Git status.
4. Check for secrets.
5. Update `HANDOVER.md`.
6. Commit.
7. Push.
8. Verify the push.
9. Report the commit hash and push result.

---

## 6. Reporting format — the only one

Use this at the end of every stage, and whenever reporting progress:

```
STAGE COMPLETE — Stage <n>: <name>

What changed
- files created / changed / removed, one line each

Tests
- command(s) run → result (e.g. 891 passed · ruff clean · mypy clean)

Needs your decision
- anything blocking or requiring approval, or "Nothing — awaiting approval"
```

Then STOP and wait. Do not continue automatically.

---

## 7. Context and token efficiency

- **Do not reread or restate** `CLAUDE.md` or `docs/HANDOVER.md` content that is
  already in context. Reread only if the file changed.
- **Do not repeat requirements back** to the user.
- **No lengthy explanations** unless asked. Short, structured, bullets and tables.
- **Inspect only files relevant** to the current task. Use targeted reads and search
  rather than whole-file reads of large files.
- **Do not reproduce** large files, logs or full diffs in responses — summarise, and
  quote only the lines that matter.
- Read `docs/PROJECT_PLAN.md` only for the current stage, once per stage.
- **Report only:** what changed, test result, and anything that needs a decision.

---

## 8. When unsure

Stop and ask **one** question. Don't guess and don't go out of scope. Ask before big
or hard-to-reverse changes.
