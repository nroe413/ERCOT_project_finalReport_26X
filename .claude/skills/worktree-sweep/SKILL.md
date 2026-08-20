---
name: worktree-sweep
description: >-
  Sweep every .claude worktree of the NateRoe_ERCOT_Project repo for new
  experimental work (new commits, updated PLAN/FINDINGS docs, new experiment
  dirs, unpushed branches) and fold the findings CONCISELY into the 26X
  Experiment Compendium on the 26Xreport branch. Use when the user asks to
  check the other worktrees, sync the compendium/summary with recent work,
  asks "what's new in the experiments", or when a scheduled sweep fires.
---

# Worktree sweep → concise compendium update

Purpose: keep `26Xreport:report_26X/experiment_compendium/` (the master
step-by-step experimental record) current with work happening in the other
Claude worktrees, without anyone having to remember to sync it.

## Style rule (hard requirement from the user)

**Concise descriptive explanations only — no paragraphs upon paragraphs.**
Every update is 1–3 lines: what changed, the headline number(s), where it
lives (branch · dir · commit). Change-log entries are single bullets. If a
finding overturns an existing compendium claim, fix that claim in place with
the same brevity (the compendium's Question/Setup/Procedure structure stays;
only Results/Conclusion lines change).

## The worktree map (as of 2026-07-26)

All under `C:\UT_research\NateRoe_ERCOT_Project\.claude\worktrees\`:

| worktree | branch | carries |
|---|---|---|
| `sharp-jackson-1e89b8` | `claude/sharp-jackson-1e89b8` (content = `origin/SOW_task_4` tip) | energy-TSA program: `experiments/cct_*`, goal-2 engines, `documentation/cct_theory_audit/` |
| `compassionate-banach-aa8040` | `GFL_breakPoint_test` | GFL breakpoint: `experiments/fault_3PG_bus14_*GFL/`, `documentation/gfl_lvrt_findings/FINDINGS.md` |
| `gfm-model-quality-inertia-f78292` | `claude/gfm-model-quality-inertia-f78292` | OpenIBR (Heron BESS) campaign: `openibr_campaign/` (PLAN.md, TESTING_WRITEUP.md) |
| `upbeat-jones-67c8d3` | `26Xreport` | the report branch (deck, compendium, vendored sources) — the sweep's WRITE target |
| `gfm_validation_task_2_ro` | detached (read-only) | REGFM_A1 MQT reference — rarely changes |
| repo root `C:\UT_research\NateRoe_ERCOT_Project` | `SOW_task_4` (often stale) | ignore unless it moved |

New worktrees appear over time — always start from `git worktree list`, not
this table. Sessions may also hold relevant context:
`mcp__ccd_session_mgmt__list_sessions` / `search_session_transcripts`
(running sessions in a worktree = results may be in flight; say so rather
than guessing).

## Procedure

1. **Load state.** Read
   `report_26X/experiment_compendium/sweep_state.json` on the `26Xreport`
   checkout (worktree `upbeat-jones-67c8d3`; `git checkout 26Xreport` there
   if it was switched away — committed work is safe on origin). The file maps
   worktree → last-seen commit + date.
2. **Enumerate.** `git worktree list` from any checkout. For each worktree:
   current branch, `git log --oneline <last-seen>..HEAD` (commit messages in
   this repo are information-dense — often sufficient by themselves),
   `git status --short` (uncommitted work), ahead/behind vs its origin
   branch.
3. **Read what changed.** For worktrees with new commits or dirty state:
   check mtimes of `PLAN.md` / `FINDINGS.md` / `TESTING_WRITEUP.md` /
   `*.tex` docs and new `experiments/*` dirs; read only the new/changed
   sections (grep headings, read tails). Never read raw run data.
4. **Decide significance.** New results, changed verdicts, new campaigns,
   doctrine rulings → compendium update. Pure scaffolding/refactors → change
   log only.
5. **Update the compendium** (`26X_experiment_compendium.tex`):
   - Append one dated bullet per finding to the `Change log` section
     (newest first).
   - Amend affected experiment subsections' Results/Conclusion lines in
     place. Keep the status table and quoting-doctrine section true.
   - Recompile: two passes of
     `C:\Users\roena\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe
     -interaction=nonstopmode 26X_experiment_compendium.tex`; delete
     aux/log/toc.
6. **Deck consistency (only if contradicted).** If a slide in
   `report_26X/26X_Report_Figure_Storyboard.pptx` now states something false,
   fix the minimal bullet(s) in `make_storyboard_deck.py` and rebuild with
   `C:\Users\roena\anaconda3\python.exe report_26X/make_storyboard_deck.py`
   (never bare `python`; never PowerPoint COM — see the memory
   `powerpoint-com-quit-hazard`).
7. **Vendor refresh (only what the compendium cites).** Re-copy changed
   docs/plots into `experiments/` / `documentation/` on 26Xreport using the
   established tar-with-excludes pattern (`*.csv *.out *.inf *.log *.aux
   *.zip *.bak* __pycache__ *.gf46`). Nothing over ~90 MB.
8. **Unpushed results.** If a worktree branch has unpushed commits or a
   results campaign sitting uncommitted, flag it in the summary; push only
   with the standing conventions (size-check first; raw data stays
   off-repo).
9. **Save state + push.** Update `sweep_state.json` (worktree → commit,
   ISO date), commit everything on 26Xreport with a `docs(26X): worktree
   sweep <date>` message, push `origin 26Xreport`.
10. **Report.** A short table or bullet list: worktree → what's new (one
    line each) → what was updated. If nothing changed anywhere: say exactly
    that in one line and update only the state file's date (no commit needed
    unless state moved).

## Cautions

- Other sessions may be live in these worktrees: never switch their
  branches, never commit in them (except a user-sanctioned results push),
  never touch PSCAD/PowerPoint.
- In-flight runs (ladder logs growing, sessions running) → report "in
  flight", don't record partial numbers as results.
- Pre-registration discipline: a `setup.json`/PLAN hypothesis is not a
  result; only record measured outcomes.
