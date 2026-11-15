---
paths:
  - "src/api/**/*"
---

# API Route Rule

API route handlers must be async functions returning a `Response` object.
Place all route definitions under `src/api/` with one file per route group.
Validate request bodies with Zod schemas before processing business logic.
Return errors as `{ "error": "...", "message": "..." }` JSON envelopes.
Set appropriate HTTP status codes (200, 201, 400, 404, 500) on every response.
Log structured errors using `logger.error` with request ID and context fields.
Never return raw stack traces or internal error details to API clients.
Use explicit error returns instead of throwing exceptions in route handlers.
Add OpenAPI documentation comments to every public endpoint definition.
Name route handler functions with the `handle` prefix (e.g. `handleCreateOrder`).