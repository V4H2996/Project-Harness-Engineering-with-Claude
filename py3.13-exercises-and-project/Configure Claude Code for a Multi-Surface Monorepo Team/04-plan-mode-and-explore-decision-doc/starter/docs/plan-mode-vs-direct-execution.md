# Plan mode vs. direct execution — team decision guide

Choosing between Claude Code's **plan mode** (investigate and propose before changing anything) and **direct execution** (change code immediately) is the single biggest leverage point in how the team uses the harness day-to-day. The wrong mode at either extreme costs us: plan mode for trivial fixes is friction; direct execution for architectural changes burns context and produces rework.

> Anchor talk: Knight-Webb, "SWE Is Becoming Plan and Review." This is Module 8 of the Knight-Webb curriculum, the anchor talk that frames planning-before-building as the default for non-trivial changes.

This doc walks four concrete decisions against our codebase: one plan-mode example, one direct-execution example, one Explore-subagent example, and one combined-workflow example.

---

## 1. Plan-mode example

**Scenario.** Extract the duplicated cart logic (`fetchCart` + `useMemo` total + `setQuantity` handler) shared by three components into a single shared hook.

**Files touched.**
- `src/components/Cart/Cart.tsx`
- `src/components/Checkout/Checkout.tsx`
- `src/components/MiniCart/MiniCart.tsx`

The extraction target src/hooks/useCart.ts does not exist yet, so I reference it in prose only.

**Why plan mode.**
- Multi-file modification across three surfaces
- Multiple valid approaches (hook location, argument shape, return shape)
- Architectural decision about where shared logic lives
- Planning first **prevents costly rework**: refactoring three components in parallel without a shared contract risks inconsistent behavior and forces a second cleanup pass.

**Plan-mode workflow.**
1. Investigate all three call sites.
2. Propose `useCart(userId)` and the migration plan.
3. Team approves the contract.
4. Execute the refactor across the three files.

---

## 2. Direct-execution example

**Scenario.** Add a `min: 0` validation to the quantity field in the orders create handler.

**File changed.** `src/api/orders/handler.ts` — one function, `handle`.

**Why direct execution.** This is a simple, well-scoped change targeting one function. I can describe the diff in one sentence ("reject line items whose quantity is below zero") and predict the patch before invoking Claude, so I skip planning and go straight to execution.

---

## 3. Explore-subagent example

**Scenario.** Find every place we call `processRefund` across the codebase so we can audit refund reasons.

**Discovery targets.** `src/services/payment.ts`, `src/api/orders/refund.ts`, `src/api/billing/issue.ts`.

**Why Explore.** This is a discovery task with verbose intermediate output (greps, file reads, call-site snippets). An Explore subagent isolates that verbose discovery output and returns a summary, keeping it out of the main conversation context.

**Scratchpad pattern.** The Explore agent writes its working notes to a scratchpad file (`tmp/refund-callsites.md`) so the inventory survives the main session's context window. This is the scratchpad pattern: discovery output lives in the scratchpad, not in the primary thread.

---

## 4. Combined workflow — plan mode for investigation, then direct execution

**Scenario.** Rename `ordersRepo.findById` → `ordersRepo.getById` in `src/db/orders.ts` to align with the team naming convention (`get*` for single-row reads, `find*` for multi-row).

**Why combine.** The investigation question — where is `findById` called, and are any call sites dynamic (constructed string lookups grep would miss)? — suits plan mode. Once the call-site list is in hand, the rename itself is mechanical: direct execution.

**Flow.**
1. Plan mode: investigate and propose (plan mode for investigation).
2. You approve the plan.
3. Direct execution: apply the rename across call sites and run tests (plan mode → direct execution).

This combined workflow shows plan mode and direct execution aren't binary: investigation first, mechanical change second.

---

## Quick reference

| Situation | Mode |
|-----------|------|
| Single function, fix is obvious, you can predict the diff | Direct execution |
| Multi-file refactor, API shape is debatable | Plan mode |
| Discovery / inventory across the codebase, you'll throw away the intermediate steps | Explore subagent |
| Investigation-then-mechanical-change | Plan mode → direct execution |
| Architectural decision (which database, which queue) | Plan mode, possibly with a fork to compare options |

When in doubt: plan mode is recoverable (you can switch to execution), but direct execution on a complex change is not. Default to plan when uncertain.