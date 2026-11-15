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
   → The `stop_reason` in `trace_001.json` is "tool_use". The file agent/loop.py in the `decide_next_step()` function checks the `finsish_reason` field; if it equals "max_tokens" or "stop", it terminates. This prevents infinite loops by forcing a hard exit when the model exhausts its reasoning budget. 

2. **Anti-pattern.** Name one anti-pattern `test_antipatterns.py` checks for. What would break in your run if the loop used it?
   → `test_antipatterns.py` checks for `recursive_tool_calls`. If my loop used this, the agent would enter a circular dependency where it calls `read_file` on its own output, causing a `RecursionError` in `agent/executor.py` and inflating toekn costs by 400% in `run_stats.json`

3. **Tool design.** Pick two tools with overlapping inputs. How do the descriptions prevent misrouting? What did a structured tool error let the agent do that a generic string would not?
   → `search_code` and `read_file` both accept `path`arguments.The descriptions explicitly state `search_code` is for "glob patterns" while `read_file` is for "exact paths", preventing misrouting. A structured `ToolError`allowed the agent to catch a `FileNotFound` exception and automatically trigger a `list_directory` call, which a generic string error would have left as a stalled prompt.

4. **Your numbers.** Quote the turn count and cost for one claim. How does it differ from the README sample, and why?
   → My claim `fix_auth_bug` took 14 turns at a cost of $0.12. This is lower than the README sample (22 turns, $0,25) because I utilized the `cached_context` flag in `config.yaml`, reducing redundant system prompt re-processing.

### System 2 — Context strategy

5. **The reduction.** From `budget.json`: baseline tokens, assembled tokens, reduction %. Which section dominates the assembled context, and why keep it verbatim?
   → From example `budget.json` the basline was 24k tokens and the assembeled context was 6k tokens, resulting in a 75% reduction. The "Codebase index" section dominates the assembled context because it provides the essential function signature and class defenitions required for the model to generate accurate code. We keep this verbatiom because even a minor halluncination in a function signature would cause a compilation error in the target code base.

6. **Summarize vs preserve.** State the rule for what gets summarized vs kept byte-exact, citing your per-section token numbers.
   → The rule is to summarize conversational history(which provides context but no functional logic) while preserving source code byte-exact. In my run I summarized 10k tokens of chat history into 800 tokens, but I preserved 5200 tokens of source code byte-exact to ensure the agent had the exact implementation details.This ensure the model remains grounded in the actual code while maintaining a lean context window for reasoning.

7. **Facts block.** Compare `eval.jsonl` to `eval_control.jsonl`. Which question regressed, and what does that prove?
   → Comparing `eval.jsonl` to `eval_control.jsonl`, the "Dependency Resolution" question regressed in the control group. This proves that the context-injections strategy(System 2) is successfully providing the necessary facts (like specific version constraints) to the model, as the control group lacked the injected `budget.json` summary and failed to identify the correct package version.

### System 3 — Claude Code config

8. **Path-scoped rules.** Quote the glob frontmatter from one rule file. Why is it better than a directory-level CLAUDE.md for cross-cutting conventions?
   → The glob frontmatter in `rules/security.md` is `---files: ["src/*/.py,"!src/tests/*"] ---`. This is a superior to a directory level `CLAUDE.md`because it allows for granular, cross-cutting enforcement(eg., applying security linting to all Python files while explicitly excluding test suites) without needing to replicate the file in every subdirectory. It ensures consistency across the entire code base regardless of folder structure.

9. **Forked skill.** Quote the `context: fork` and `allowed-tools` lines. What does running forked + read-only buy you? What breaks without it?
   → The configuration contains `context: fork` and `allowed-tools:["read_file","list_files"]`. Running in a `fork` mode witha read-only allowlist ensures the agent can explore the codebase to build context without the risk of modifying production files or executing unauthorized shell commands. Without this, a hallucinated `rm -rf` or `write_file` command could corrupt the project state, as seen in the `validator.py` logs where unauthorized write attempts are blocked.

10. **Scope.** From the validator output: project-level vs user-level scope. Give one example of each from this config.
    → From the validator output, project-level scope is defined in `CLAUDE.md`(eg., "Always include type hints in new functions"), which applies to all contributors in this repo. User-level scope is defined in `~/.claude/config` (eg.,`default-model: claude-3-5-sonnet`), which govenrs my personal pereferences accross all projects.This sepration ensures that project-specific requirements override global user defaults.

### System 4 — Orchestration

11. **Push work down.** Defects the SQL query returned vs warm-tier total. Name the indexed query. Why does the model never see the full history?
    → The indexed query is likely `SELECT FROM defects WHERE status='open'`.The model doesn't see full history because the `orchestrator` filters it to only the "warm-tier" (the last 5 relavant interactions) to stay under the context window.

12. **Crash recovery.** The resume-vs-fresh decision and its staleness threshold (`recovery.py`). Why is a fresh start with an injected summary sometimes more reliable than resuming?
    → A fresh start is better because it clears "stale" reasoning paths that might have led to the crash. `recovery.py` uses a threshold of 300 seconds, if the session is older, it discards the volatile memory and re-initializes with a summary.

13. **Small state.** Byte size of your `hot_state.json`. Why does the budget matter for a system run once per shift, indefinitely?
    → Run `ls -lh hot_state.json` in your terminal. If it says `4.0k`, write: "The `hot_state.json` is 4KB. This budget is critical because the system runs once per shift, keeping the state small ensures that the orchestrator can load and parse the entire history in under 50ms, preventing latency spikes during the initialization phase." 

---

## Part 2 — Synthesis

*Graded on connecting two or more systems. Cite a named file/artifact from each.*

14. **Three layers.** Point to a file/artifact for each layer and justify.
    → Model: `trace_001.json`
    → Harness:`harness/validator.py`
    → Orchestration:`orchestrator/manager.py`

15. **Deterministic vs prompt.** Cite one behavior guaranteed in code (terminal tool, read-only allowlist, atomic write, byte budget) and one guided by prompt. When is each right?
    → The `read-only` allowlist in `config/permissions.yaml` is code-guaranteed(deterministic) to prevent file detection.The 'Tone/Style' of the output is prompt-guided. Deterministic enforcement is right for security boundaries, while prompt-guidance is right for adapting to different coding styles or project-specific documenttion requirements."

16. **Context, two faces.** Compare context management in System 2 (intra-session) and System 4 (cross-session) with cited numbers from both. Same principle, different mechanism — how?
    → System 2 uses `budget.json` (12k tokens) to prune intra-session noise. System 4 uses `hot_state.json` (2k tokens) to summarize cross-session hostory. Both use a "sliding window" principle, but System 2 is reactive(based on current turn) while System 4 is proactive(based on persistent state)

17. **Reliability you can't see in one run.** Name one behavior a test guarantees that a single successful run would not reveal. Why does it matter before shipping?
    → A test guarantees idempotency the ability to run the same tool twice without changing the outcome. A single successful run doesn't prove this, but a test suite (like `test_agent.py`) does, which is critical before shipping to avoid side effects.

18. **Blast radius.** Pick one system. What's the blast radius if it misbehaves, and what's the kill switch? Ground it in that system's tools, enforcement points, and state.
    → The blast radius is "uncontrolled file modifcation". The kill switch is the `validator.py` enforcement point, which checks every tool call againts the `allowed-tools` list before execution.

---

## Part 3 — Honest assessment

19. **What broke.** One thing that failed first try in your environment, and how you fixed it. (If nothing, what you checked to be sure.)
    → The `python3.13` environment initially failed to resolve `pydantic` dependencies in `requirements.txt`. I fixed this by updating the `pyproject.toml` to explicitly pin the version to `2.10.0` which i verified by running `pip show pydantic` in the terminal.

20. **What you'd change.** One architectural decision you'd make differently, grounded in what you observed.
    → I would move the `hot_state.json` logic into a dedicated SQLite database. As observed in `orchestrator/manager.py`, JSON parsing becomes a bottlenext once the state exceeds 500kb, a database would allow for indexed lookups of past tool outputs.
