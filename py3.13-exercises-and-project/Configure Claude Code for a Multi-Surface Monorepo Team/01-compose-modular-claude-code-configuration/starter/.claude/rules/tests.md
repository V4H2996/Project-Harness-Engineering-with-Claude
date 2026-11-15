---
paths:
  - "**/*.test.tsx"
  - "**/*.test.ts"
---

# Test Rule

Test files must use `describe` and `it` blocks to organize test cases.
Colocate tests as `Component.test.tsx` next to source files.
Mock external dependencies with `vi.mock` from the vitest testing library.
Use `expect(...).toBe(...)` or `expect(...).toEqual(...)` for assertions.
Avoid `console.log` statements inside test cases and test files.
Name test cases descriptively so failure messages are self-explanatory.
Group related assertions inside `describe` blocks with clear context strings.
Test both success and failure paths for every exported function.
Use `beforeEach` and `afterEach` for test setup and teardown logic.
Keep each test file under 300 lines; split into multiple files when larger.