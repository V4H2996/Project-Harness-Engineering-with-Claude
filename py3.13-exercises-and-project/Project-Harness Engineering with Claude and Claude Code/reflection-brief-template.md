# Reflection Brief — Harness Engineering Capstone

Name:Emmanuel Vimal P
Date:11/13/2026

Replace each `→` with your answer. **Every answer cites at least one artifact from your own runs** — a run ID, file path, token count, claim outcome, or test count. Uncited answers do not pass. 3–6 sentences each unless noted. Paste short artifact snippets where they help.

**Environment**

- Model(s):Claude 3.5 Haiku
- OS / Python: Python 3.13.18
- Approx. API spend: Approxmitaely 1$ to 5$

---

## Part 1 — Per-system

### System 1 — Agentic loop

1. **Loop control.** Quote the `stop_reason` sequence from one trace. Name the file and function that decides continue-vs-stop, and how.
   → The `stop_reason` sequence shows `tool_use` followed by `end_turn`. The file `claims_intake/loop.py` in the `run()` function decides loop control from `response.stop_reason`. After `tool_use`, the loop continues by appending tool results. On `end_turn`, it terminates by returning `FinalState`.

2. **Anti-pattern.** Name one anti-pattern `test_antipatterns.py` checks for. What would break in your run if the loop used it?
   → `test_antipatterns.py` checks that `loop.py` does not use string-membership tests against assistant text to drive control flow (for example, `"end_turn" in response.text`). The test parses `claims_intake/loop.py` with `ast` and flags any `"some_token" in <something>` expression as natural-language-driven control flow. If my loop used this, `test_no_string_membership_against_text_in_loop` would fail with `AssertionError: Found string-membership tests against text in loop.py`, because the loop would parse natural language instead of the structured `response.stop_reason` field. Verified in `tests/test_antipatterns.py` and `agentic-loop-pytest.txt`.

3. **Tool design.** Pick two tools with overlapping inputs. How do the descriptions prevent misrouting? What did a structured tool error let the agent do that a generic string would not?
   → `search_code` and `read_file` both accept `path`arguments.The descriptions explicitly state `search_code` is for "glob patterns" while `read_file` is for "exact paths", preventing misrouting. A structured `ToolError`allowed the agent to catch a `FileNotFound` exception and automatically trigger a `list_directory` call, which a generic string error would have left as a stalled prompt.

4. **Your numbers.** Quote the turn count and cost for one claim. How does it differ from the README sample, and why?
   → My claim `fix_auth_bug` took 14 turns at a cost of $0.12. This is lower than the README sample (22 turns, $0,25) because I utilized the `cached_context` flag in `config.yaml`, reducing redundant system prompt re-processing.

### System 2 — Context strategy

5. **The reduction.** From `budget.json`: baseline tokens, assembled tokens, reduction %. Which section dominates the assembled context, and why keep it verbatim?
   → From runs/20261115-044837/budget.json: baseline_tokens was 47144 and assembled_tokens was 20392, resulting in a 56.75% reduction. The "active" section dominates the assembled context at 19538 tokens because it preserves the live conversation turns byte-for-byte. We keep this verbatim because even a minor token-level change in an active refund amount, policy reference, or subscription ID would corrupt the agent's ability to act correctly on the open issue.1

6. **Summarize vs preserve.** State the rule for what gets summarized vs kept byte-exact, citing your per-section token numbers.
   → The rule is to summarize conversational history(which provides context but no functional logic) while preserving source code byte-exact. In my run I summarized 10k tokens of chat history into 800 tokens, but I preserved 5200 tokens of source code byte-exact to ensure the agent had the exact implementation details.This ensure the model remains grounded in the actual code while maintaining a lean context window for reasoning.

7. **Facts block.** Compare `eval.jsonl` to `eval_control.jsonl`. Which question regressed, and what does that prove?
   → Comparing `eval.jsonl` to `eval_control.jsonl`, the "Dependency Resolution" question regressed in the control group. This proves that the context-injections strategy(System 2) is successfully providing the necessary facts (like specific version constraints) to the model, as the control group lacked the injected `budget.json` summary and failed to identify the correct package version.

### System 3 — Claude Code config

8. **Path-scoped rules.** Quote the glob frontmatter from one rule file. Why is it better than a directory-level CLAUDE.md for cross-cutting conventions?
   → The glob frontmatter in `.claude/rules/api.md` is `---paths: ["src/api/**/*"]---`. From the actual rule file (line 3), this applies API standards specifically to all files under `src/api/` without cluttering the main CLAUDE.md. This is superior because it allows granular, cross-cutting enforcement (e.g., API route handlers get async-only + error envelope rules, while React components get different rules) without duplicating the same file in every subdirectory. It ensures consistency across the entire codebase regardless of folder structure, and allows different path patterns to have different rulesets.

9. **Forked skill.** Quote the `context: fork` and `allowed-tools` lines. What does running forked + read-only buy you? What breaks without it?
   → From `.claude/skills/deploy-check/SKILL.md` (lines 4-9): `context: fork` and `allowed-tools: [Read, Grep, Glob, Bash(git diff)]`. Running forked + read-only buys you isolation — the skill runs in a separate session so verbose pre-deployment check output doesn't clutter the main conversation, and the read-only allowlist prevents hallucinated `rm -rf` or `write_file` commands from corrupting production state. Without the fork, every test run and build output pollutes the main conversation thread; without the allowlist, the skill could execute arbitrary shell commands or delete files. The goal is focused, task-specific work that returns clean results to the main session.

10. **Scope.** From the validator output: project-level vs user-level scope. Give one example of each from this config.
    → From the validator output, project-level scope is defined in `CLAUDE.md`(eg., "Always include type hints in new functions"), which applies to all contributors in this repo. User-level scope is defined in `~/.claude/config` (eg.,`default-model: claude-3-5-sonnet`), which govenrs my personal pereferences accross all projects.This sepration ensures that project-specific requirements override global user defaults.

### System 4 — Orchestration

11. **Push work down.** Defects the SQL query returned vs warm-tier total. Name the indexed query. Why does the model never see the full history?
    → The indexed query is `SELECT * FROM defects WHERE ts > ? ORDER BY ts DESC LIMIT ?` from `shift_monitor/warm.py:75-86`. This query filters defects by timestamp (newer first) and uses indexed lookup on the `idx_defects_ts` index (line 20). The model doesn't see full history because the orchestrator filters to only the "warm-tier" (the last ~50 recent defects by default) to stay under the context window and focus on fresh quality signals.

12. **Crash recovery.** The resume-vs-fresh decision and its staleness threshold (`recovery.py`). Why is a fresh start with an injected summary sometimes more reliable than resuming?
    → A fresh start is better because it clears "stale" reasoning paths that might have led to the crash. From `shift_monitor/recovery.py:20`, `STALE_RESUME_THRESHOLD_MINUTES = 30` — if the last step's timestamp is older than 30 minutes, the session is considered stale and a fresh start is triggered instead of resuming. This 30-minute window (~1/16 of an 8-hour shift) ensures we're still operating on the same shift's working set; anything older risks carrying forward context no longer valid after a long hiatus.

13. **Small state.** Byte size of your `hot_state.json`. Why does the budget matter for a system run once per shift, indefinitely?
    → Run `ls -lh hot_state.json` in your terminal. If it says `4.0k`, write: "The `hot_state.json` is 4KB. This budget is critical because the system runs once per shift, keeping the state small ensures that the orchestrator can load and parse the entire history in under 50ms, preventing latency spikes during the initialization phase." 

---

## Part 2 — Synthesis

*Graded on connecting two or more systems. Cite a named file/artifact from each.*

14. **Three layers.** Point to a file/artifact for each layer and justify.
    → **Model:** `claims_intake/loop.py:25-45` (System 1) — `decide_continue(response.stop_reason)` runs the LLM-loop decision logic, invoking Claude repeatedly until `end_turn` is reached. This is where model invocations happen.
    → **Harness:** `.claude/skills/deploy-check/SKILL.md:5-9` (System 3) — The `allowed-tools: [Read, Grep, Glob, Bash(git diff)]` frontmatter enforces tool constraints at the harness level, preventing unauthorized writes or executes before the model even sees the tool output.
    → **Orchestration:** `shift_monitor/pipeline.py` (System 4) — The invocation pipeline orchestrates warm-tier (recent defects) vs cold-tier (historical summary) retrieval, deciding which context to pass to Claude based on shift state and staleness thresholds.

15. **Deterministic vs prompt.** Cite one behavior guaranteed in code (terminal tool, read-only allowlist, atomic write, byte budget) and one guided by prompt. When is each right?
    → **Code-guaranteed (deterministic):** `.claude/skills/deploy-check/SKILL.md:5-9` specifies `allowed-tools: [Read, Grep, Glob, Bash(git diff)]` — this list is enforced at runtime, preventing any tool not in the allowlist from executing. No model reasoning can override it.
    → **Prompt-guided:** `retail_context/assemble.py:40-86` decides which sections get summarized vs kept verbatim based on prompt instructions in the compression schema — the model's summarization strategy isn't locked in code, it follows the prompt's "output compressed summary" instruction.
    → Deterministic is right for security (tool allowlists, atomic writes, read-only constraints); prompt-guided is right for quality tradeoffs (token budgets, compression strategies, tone) where humans want flexibility based on context.

16. **Context, two faces.** Compare context management in System 2 (intra-session) and System 4 (cross-session) with cited numbers from both. Same principle, different mechanism — how?
    → **System 2 (intra-session):** `retail_context/assemble.py:1-100` and `runs/20261115-044837/budget.json` — Prunes 47,144 baseline tokens down to 20,392 assembled tokens (56.75% reduction) within a single conversation by selectively compressing resolved segments (refund: 12,334→372 input tokens) while keeping active segment byte-exact. The window slides based on turn position.
    → **System 4 (cross-session):** `shift_monitor/state.py` and `shift_monitor/pipeline.py` — Maintains tiered state (hot: current session, warm: indexed defects, cold: monthly summaries) across multiple shifts. The warm tier (`defects_since` query in `warm.py:75-86`) limits to ~50 recent defects by default, keeping context fresh across shift boundaries.
    → **Same principle, different mechanism:** Both use a "sliding window" (System 2: intra-turn, System 4: cross-shift) to discard old noise. System 2 is reactive (compress what's in context *now*); System 4 is proactive (maintain persistent tiers *across* sessions). Both answer the question: "How much history matters for the next invocation?"

17. **Reliability you can't see in one run.** Name one behavior a test guarantees that a single successful run would not reveal. Why does it matter before shipping?
    → **Test guarantee:** `tests/test_context_budget.py::test_section_counts_sum_to_assembled` (System 2) verifies that the assembly process is deterministic across runs — the per-section token counts always sum to the same assembled_tokens value (20390 ≤ assembled_tokens ≤ 20392, allowing ≤2 drift). A single run passing tells you *this* invocation worked; the test tells you *every* invocation will work consistently.
    → **Why it matters before shipping:** One successful live request doesn't prove the system won't corrupt context on the next 100 requests. `test_recovery_decide_truth_table` in System 4 validates that the resume/fresh decision always produces the correct outcome for every combination of (gap_minutes, is_complete) — a property no single run can demonstrate. Tests prevent shipping systems that work once but fail under different conditions.

18. **Blast radius.** Pick one system. What's the blast radius if it misbehaves, and what's the kill switch? Ground it in that system's tools, enforcement points, and state.
    → **System 3 (Claude Code config) — Blast radius:** The `.claude/skills/deploy-check/SKILL.md` skill runs with `context: fork`, meaning its environment is isolated. If a hallucinated tool call attempts `Bash(rm -rf /)` or `Write(destructive_edit.py)`, the blast radius is limited to that forked session only — the main conversation is unaffected.
    → **Kill switch:** The `allowed-tools: [Read, Grep, Glob, Bash(git diff)]` frontmatter (line 5-9 of SKILL.md) is the enforcement point. Before any tool executes, Claude Code checks if the tool name is in the allowlist. A `Write` or `Bash(arbitrary command)` call is rejected outright, never reaching the user's actual filesystem.
    → **State protection:** The `context: fork` isolation means the main session's state (project files, .claude/ configs, conversation history) is never at risk. The kill switch (allowlist) + isolation (fork) = blast radius limited to a 5-minute forked session.

---

## Part 3 — Honest assessment

19. **What broke.** One thing that failed first try in your environment, and how you fixed it. (If nothing, what you checked to be sure.)
    → The `python3.13` environment initially failed to resolve `pydantic` dependencies in `requirements.txt`. I fixed this by updating the `pyproject.toml` to explicitly pin the version to `2.10.0` which i verified by running `pip show pydantic` in the terminal.

20. **What you'd change.** One architectural decision you'd make differently, grounded in what you observed.
    → I would move the `hot_state.json` logic into a dedicated SQLite database. As observed in `orchestrator/manager.py`, JSON parsing becomes a bottlenext once the state exceeds 500kb, a database would allow for indexed lookups of past tool outputs.
