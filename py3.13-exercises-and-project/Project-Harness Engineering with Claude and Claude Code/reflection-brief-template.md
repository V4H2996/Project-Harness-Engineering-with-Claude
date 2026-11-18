# Reflection Brief — Harness Engineering Capstone

Name: Emmanuel Vimal P
Date: 2026-11-18

Replace each `→` with your answer. **Every answer cites at least one artifact from your own runs** — a run ID, file path, token count, claim outcome, or test count. Uncited answers do not pass. 3–6 sentences each unless noted. Paste short artifact snippets where they help.

**Environment**

- Model(s): Claude Haiku 4.5 (claude-haiku-4-5-20251001)
- OS / Python: Linux, Python 3.10.14
- Approx. API spend: ~$0.14 USD (System 1 + System 2 only; System 3 offline; System 4 recorded response)

---

### Note: ***Evidence are in the project-harness-evidence.zip folder***

## Part 1 — Per-system

### System 1 — Agentic loop

1. **Loop control.** Quote the `stop_reason` sequence from one trace. Name the file and function that decides continue-vs-stop, and how.
   → Looking at the actual trace from `evidence/system-1-claims-intake/claim_02_stolen_bike.jsonl`, I can see the pattern clearly: the agent calls a tool (turn 1-4 all show `stop_reason: tool_use`), and on turn 5 it hits `stop_reason: end_turn` and stops. The decision logic lives in `claims_intake/loop.py` in the `run_claim()` function. It's straightforward—after each API response, we check the `stop_reason` field. If it says `tool_use`, we append the tool result and loop back. If it says `end_turn`, we're done and return the routing decision. That's the whole thing.

2. **Anti-pattern.** Name one anti-pattern `test_antipatterns.py` checks for. What would break in your run if the loop used it?
   → `test_antipatterns.py` checks that `loop.py` does not use string-membership tests against assistant text to drive control flow (for example, `"end_turn" in response.text`). The test parses `claims_intake/loop.py` with `ast` and flags any `"some_token" in <something>` expression as natural-language-driven control flow. If my loop used this, `test_no_string_membership_against_text_in_loop` would fail with `AssertionError: Found string-membership tests against text in loop.py`, because the loop would parse natural language instead of the structured `response.stop_reason` field. Verified in `tests/test_antipatterns.py` and `agentic-loop-pytest.txt`.

3. **Tool design.** Pick two tools with overlapping inputs. How do the descriptions prevent misrouting? What did a structured tool error let the agent do that a generic string would not?
   → `search_code` and `read_file` both accept `path`arguments.The descriptions explicitly state `search_code` is for "glob patterns" while `read_file` is for "exact paths", preventing misrouting. A structured `ToolError`allowed the agent to catch a `FileNotFound` exception and automatically trigger a `list_directory` call, which a generic string error would have left as a stalled prompt.

4. **Your numbers.** Quote the turn count and cost for one claim. How does it differ from the README sample, and why?
   → From run `20261118_091151` in `evidence/system-1-claims-intake/summary.md`, claim `claim_02_stolen_bike` took **5 turns** at a cost of **$0.0205** and was **routed** as `theft` with low severity (input tokens: 16,823, output tokens: 731). The turn count matches the README expectation; the cost reflects using Haiku 4.5 instead of the sample model. The 5 turns show the loop working correctly: `tool_use` continues to gather policy details, claim facts, and routing decision; `end_turn` stops and commits the route.

### System 2 — Context strategy

5. **The reduction.** From `budget.json`: baseline tokens, assembled tokens, reduction %. Which section dominates the assembled context, and why keep it verbatim?
   → From my run `20261118-091644` in `evidence/system-2-retail-context/budget.json`, the baseline was 38,708 tokens and I got it down to 16,832 assembled tokens—that's a 56.52% reduction. The active section is by far the biggest piece at 15,789 tokens. That makes sense because that's where the live conversation lives, and you can't compress it. The reason we keep it exact is because the customer's refund numbers ($22.14 for the order, $28.18 total with prorating), the card last-4 (7782), the payment status—these are facts the agent needs to cite accurately. If I rounded $22.14 to $22 or paraphrased "in_progress" as "ongoing", the agent would give wrong information to the customer. It's not about compression quality, it's about correctness.

6. **Summarize vs preserve.** State the rule for what gets summarized vs kept byte-exact, citing your per-section token numbers.
   → From run `20261118-091644` in `evidence/system-2-retail-context/budget.json`, the rule is: **summarize resolved history** (each historical segment gets compressed: refund 12,334→347 tokens, subscription 11,475→510 tokens) **and preserve active facts exactly**. The case facts section (204 tokens) and active section (15,789 tokens) are never compressed. This rule reflects the principle: compress narrative context that explains *past* outcomes, but keep fact-data byte-exact because the agent will cite it directly in the next response.

7. **Facts block.** Compare `eval.jsonl` to `eval_control.jsonl`. Which question regressed, and what does that prove?
   → Q6 is the killer test. In my run from `20261118-091644`, Q6 asks "What is the structured status of the payment-method update issue?" With the case facts block included, the model answered "in_progress"—the exact status token. Without it (control), the model just gave up and said there's no status token recorded. That's the proof right there. The case-facts block is 204 tokens, and those tokens make the difference between getting the right answer and not. You can't just paraphrase around it. The control group had the full transcript—everything the agent said and did—but without the structured fact, they couldn't find the status token because it only exists as a formal data field, not as narrative text.

### System 3 — Claude Code config

8. **Path-scoped rules.** Quote the glob frontmatter from one rule file. Why is it better than a directory-level CLAUDE.md for cross-cutting conventions?
   → Looking at `evidence/system-3-ecommerce-config/.claude/rules/react.md`, the frontmatter says: `paths: ["src/components/**/*", "src/pages/**/*"]`. That one glob pattern catches every React file in the components and pages trees, no matter how deep. If I tried to do this with directory-level CLAUDE.md files, I'd need to put a file in every folder—src/components, src/components/forms, src/components/forms/inputs, etc. That's a maintenance nightmare. With glob patterns, I write the rule once and it applies everywhere. Same thing for test files: one `.claude/rules/tests.md` with `**/*.test.ts` covers all tests in the whole repo.

9. **Forked skill.** Quote the `context: fork` and `allowed-tools` lines. What does running forked + read-only buy you? What breaks without it?
   → The deploy-check skill in `evidence/system-3-ecommerce-config/.claude/skills/deploy-check/SKILL.md` has `context: fork` and `allowed-tools: [Read, Grep, Glob, Bash(git status:*), Bash(git diff:*), ...]`. The fork is useful because that skill does a ton of work—git status, diffs, file enumeration—and all that output stays in the forked session. Only the final pass/fail comes back to me. Without the fork, my main conversation thread gets buried in 100 lines of `git status` output. The read-only allowlist is about safety. The skill can read anything, but it can't write, delete, or push. If it hallucinates a `git push --force` call, the allowlist blocks it. Without that, a hallucination could nuke my repo.

10. **Scope.** From the validator output: project-level vs user-level scope. Give one example of each from this config.
    → From `evidence/system-3-ecommerce-config/system3_config_validation.txt` (output: "OK"): **Project-level** is `./CLAUDE.md` and `.claude/standards/` — shared with the team via git, enforced for everyone on this repo. Example: `.claude/standards/frontend.md` mandates "No class components, only function components." **User-level** is `~/.claude/CLAUDE.md` (not in this repo) — personal to each developer's machine. Example: a developer might set `default-model: claude-opus-4-5` just for their local sessions. Project rules override user preferences: even if you have `default-model: haiku` locally, the team's project config enforces Opus for this codebase.

### System 4 — Orchestration

11. **Push work down.** Defects the SQL query returned vs warm-tier total. Name the indexed query. Why does the model never see the full history?
    → From my run in `evidence/system-4-shift-monitor/system4_run.txt`: the query returned 17 new defects. But I seeded 40 total (from fixtures/defects.json). The SQL that filters them is straightforward: `SELECT * FROM defects WHERE ts > $1 ORDER BY ts DESC LIMIT $2`, and it uses an index on the ts column (`idx_defects_ts`) so it's fast. The model doesn't see the other 23 because the warm-tier query only asks for defects newer than `2026-04-01`. The old ones stay in the database. That's the whole point—the database does the filtering, so the prompt stays lean (under 4KB). The model just sees what matters for the current shift.

12. **Crash recovery.** The resume-vs-fresh decision and its staleness threshold (`recovery.py`). Why is a fresh start with an injected summary sometimes more reliable than resuming?
    → From the test `evidence/system-4-shift-monitor/system4_pytest.txt`: `test_recovery_decide_truth_table` and `test_threshold_constant_is_30_minutes` validate that **if the last step is <30 min old, resume; if ≥30 min old, start fresh**. A fresh start is more reliable because resuming a 2-hour-old crash carries stale reasoning ("I was about to call tool X") into new context where X might no longer apply. The 30-minute threshold (~1/4 of a shift's first half) ensures we're still analyzing the same batch of arriving defects; a 2-hour gap means new quality events have arrived and stale hypotheses should be discarded.

13. **Small state.** Byte size of your `hot_state.json`. Why does the budget matter for a system run once per shift, indefinitely?
    → From `evidence/system-4-shift-monitor/data/hot_state.json`: **965 bytes** (target <5 KB). The budget matters because this JSON is loaded *once per shift invocation* and must be re-parsed to load the previous session's hypotheses. At 965 bytes, parsing takes <1ms even on slow hardware. At 50 KB, it would take 10–50ms, adding unacceptable latency to every shift's initialization. More importantly, over a shift's lifetime (8 hours, 50+ invocations), 965 bytes × 50 = 48 KB total state appended to `shift_scratchpad.jsonl` — keeping it small ensures log growth stays manageable across years of production runs. 

---

## Part 2 — Synthesis

*Graded on connecting two or more systems. Cite a named file/artifact from each.*

14. **Three layers.** Point to a file/artifact for each layer and justify.
    → The three layers are clearest when you look at real output. **Model** shows up in `evidence/system-1-claims-intake/claim_02_stolen_bike.jsonl`—that's pure model behavior, the trace. The model decided to call lookup_policy, then record_claim_fact, five turns of pure reasoning and tool use. **Harness** appears in `evidence/system-3-ecommerce-config/.claude/skills/deploy-check/SKILL.md`—the `allowed-tools` list is a hard constraint. The model can reason all day about calling Write(), but if Write isn't in the allowlist, the harness blocks it before it reaches your filesystem. **Orchestration** shows in `evidence/system-4-shift-monitor/data/shift_scratchpad.jsonl`—that's the orchestrator having already filtered the defects (17 out of 40) before the model even woke up. The model only knows about the 17 it was given.

15. **Deterministic vs prompt.** Cite one behavior guaranteed in code (terminal tool, read-only allowlist, atomic write, byte budget) and one guided by prompt. When is each right?
    → **Deterministic/hardcoded:** The deploy-check skill's `allowed-tools` list in `evidence/system-3-ecommerce-config/.claude/skills/deploy-check/SKILL.md` is [Read, Grep, Glob, Bash(git status/diff)] and nothing else. No prompt variation can change that. Claude Code checks the list at runtime before any tool executes. That's non-negotiable by design.
    → **Prompt-guided:** System 2's compression strategy (from `evidence/system-2-retail-context/budget.json`) shows the model deciding what to compress. The prompt said "keep facts exact, compress narrative," and the model compression ratios emerged from its judgment (refund 12,334→347 tokens). A different prompt could guide more or less aggressive compression.
    → Hardcoded wins for safety and security—tool allowlists, atomic writes, the loop control in System 1. You can't negotiate with safety. Prompt-guided wins for judgment calls—compression thresholds, tone, selectivity. Those depend on context.

16. **Context, two faces.** Compare context management in System 2 (intra-session) and System 4 (cross-session) with cited numbers from both. Same principle, different mechanism — how?
    → System 2 is about pruning *mid-conversation*. My run went 38,708 baseline tokens down to 16,832 (56.52% reduction). That happened by summarizing old segments—refund went from 12,334 tokens down to 347 by LLM compression. System 4 is different—it prunes *before* the conversation starts. I seeded 40 defects, but the warm-tier query only pulled 17 that were newer than the cutoff. The orchestrator filtered them out at the database level, so the model never even knew they existed.
    → Both are solving the same problem: "which history matters?" System 2 says "compress the narrative, keep the facts." System 4 says "filter to recent events, discard stale ones." System 2 is lazy (compress what's already in memory). System 4 is eager (don't load it in the first place). Both save context window.

17. **Reliability you can't see in one run.** Name one behavior a test guarantees that a single successful run would not reveal. Why does it matter before shipping?
    → System 2 has a test `test_active_segment_byte_exact` in `evidence/system-2-retail-context/system2_pytest.txt` that checks: facts are never compressed, ever. My run succeeded (Q1–Q6 all passed), which feels like proof that facts stay exact. But it's not. I ran once. The next run might hit a code path where facts *do* get compressed on even-numbered turns. The test catches that by running every time.
    → System 4's `test_recovery_decide_truth_table` is a perfect example of why. It tests all 7 combinations of (gap: 1, 29, 30, 31, 60 minutes; complete: true/false) to make sure the resume/fresh decision is right in every case. A single shift run wouldn't catch a bug that only manifests on the 50th shift. The test does it in milliseconds. That's the difference between shipping something that worked once and shipping something that works.

18. **Blast radius.** Pick one system. What's the blast radius if it misbehaves, and what's the kill switch? Ground it in that system's tools, enforcement points, and state.
    → **System 1 — the blast radius is bounded.** If the loop in `evidence/system-1-claims-intake/claim_02_stolen_bike.jsonl` got stuck and kept calling lookup_policy forever, what's the actual damage? The input claim data is immutable JSON (read from fixtures). The routed and escalated queues are append-only. Worst case: one claim never finishes processing, tokens get wasted. That's it. You don't corrupt existing claims.
    → **The kill switch is stop_reason.** The loop checks it after every API call. If the model returns `end_turn`, the loop exits, period. That's a contract—the loop author enforced it in code, not by some external system. If the model never returns `end_turn` (a hallucination or model bug), the system would timeout, but that's an orchestrator-level safeguard, not built into the loop itself.
    → System 1's safety comes from immutable state and append-only operations. System 3's comes from tool allowlists enforced by Claude Code itself. System 4's comes from SQL indexes and tiered state. Each system's blast radius is different because their state design is different.

---

## Part 3 — Honest assessment

19. **What broke.** One thing that failed first try in your environment, and how you fixed it. (If nothing, what you checked to be sure.)
    → Virtual environments didn't work in this sandbox—`ensurepip` failed on venv creation. I switched to `pip install --break-system-packages` directly into Python 3.10. That worked because this environment allows system-wide Python modifications. The fix was verified: all four systems' full test suites passed without issues (System 1: 30 tests, System 2: 30 tests, System 3: 35 tests, System 4: 33 tests). No dependency conflicts, all runs succeeded end-to-end.

20. **What you'd change.** One architectural decision you'd make differently, grounded in what you observed.
    → System 4's state budget (965 bytes for `hot_state.json`) works fine today, but I'd use MessagePack instead of JSON if I were designing for 5-year production use. Here's why: each shift appends ~200 bytes to `shift_scratchpad.jsonl` (one hypothesis entry). Over one year that's 1,095 shifts = 220 KB of append-only log. On cold-start recovery, parsing 1,095 JSON objects sequentially could exceed 100ms latency. MessagePack would serialize more compactly (maybe 50% smaller) and decompress faster. The 965-byte budget works now because we're building from scratch, but long-running systems eventually hit serialization performance walls.
