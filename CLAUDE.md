# Bond Analytics — Claude Code Guidelines

## Changelog Rule

Every code change **must** be recorded in `frontend/src/pages/Changelog.tsx` before the commit is pushed.

- Use the next sequential `id` and a new `version` string.
- **`timestamp` must be the exact IST date and time** of the change — format: `DD MMM YYYY, HH:MM IST` (e.g. `07 Sep 2026, 21:30 IST`). Do **not** use a bare month/year like `Sep 2026`.
- Pick the appropriate `category`: Feature, Enhancement, Fix, Refactor, Security, Performance, Config, UI, Polish, or Migration.
- Write a concise `title` and bullet-point `description` entries covering what changed and why.
- The Changelog entry and the feature/fix commit should be in the **same** git commit.
