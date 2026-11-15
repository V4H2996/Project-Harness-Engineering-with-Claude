---
paths:
  - "src/components/**/*"
  - "src/pages/**/*"
---

# React Component Rule

React components must use TypeScript interfaces for props: `interface Props { ... }`.
Name components in `PascalCase` and export as default from each file.
Keep files under `src/components/` for shared UI or `src/pages/` for route-level components.
Avoid the `any` type in component signatures and prop interfaces.
Use `React.memo` for pure presentational components that receive stable props.
Name event handlers with `handleXxx` convention (for example `handleSubmit`).
Never use array index as a `key` in rendered lists; use a stable ID instead.
Prefer `useCallback` for handler references passed to memoized child components.
Document complex components with a JSDoc-style comment block above the definition.
Use `useEffect` only for synchronization, not for data transformation or prop derivation.
Keep components under 200 lines; extract sub-components when they exceed this limit.