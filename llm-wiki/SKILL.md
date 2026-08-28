---
name: llm-wiki
description: "Wiki: create a markdown knowledge base, ingest a source, answer from an existing wiki, or audit wiki integrity."
---

# Wiki

Build and maintain an interlinked markdown knowledge base. Preserve source text;
the user supplies sources and directs analysis.

## Location

Set via `WIKI_PATH` env var; defaults to `~/wiki`.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

## Structure

```
wiki/
├── SCHEMA.md      # conventions, tag taxonomy, page thresholds
├── index.md       # content catalog, one line per page
├── log.md         # append-only action log
├── raw/           # Layer 1: immutable sources (agent reads, never edits)
├── entities/      # Layer 2: people, orgs, products, models
├── concepts/      # Layer 2: concepts/topics
├── comparisons/   # Layer 2: side-by-side analyses
└── queries/       # Layer 2: filed query results worth keeping
```

## Orient (existing wiki)

1. Read `SCHEMA.md` — domain, conventions, tags.
2. Read `index.md` — what pages exist.
3. Skim recent `log.md` — recent activity.

Proceed only after all three files are read. If the directory or its root files
do not exist, initialize it instead.

## Initialize a New Wiki

1. Determine the path (`$WIKI_PATH`, or ask; default `~/wiki`).
2. Create the directory structure above.
3. Ask what domain the wiki covers.
4. Write `SCHEMA.md` (template below), `index.md`, and `log.md`.
5. Confirm the directories and root files exist, the domain and tag taxonomy are
   recorded, and `log.md` records initialization. Then suggest first sources.

### SCHEMA.md Template

```markdown
# Wiki Schema

## Domain
[What this wiki covers — e.g. "AI/ML research"]

## Conventions
- File names: lowercase, hyphens (e.g. `transformer-architecture.md`)
- Every page starts with the frontmatter below
- Link pages with `[[wikilinks]]` wherever a real relationship exists (don't pad to hit a count)
- Bump `updated` when editing a page
- Add every new page to `index.md`; append every action to `log.md`

## Frontmatter
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [from taxonomy below]
sources: [raw/source-name.md]
---

## Tag Taxonomy
[10-20 top-level tags. Add a new tag here BEFORE using it, to prevent sprawl.]

## Page Thresholds
- Create a page when something appears in 2+ sources OR is central to one
- Add to an existing page when a source mentions something already covered
- Split pages over ~200 lines (the one size threshold; referenced by Lint and Pitfalls)

## Update Policy
When new info conflicts with a page: check dates (newer usually wins); if
genuinely contradictory, note both positions with dates and sources, and flag
for user review.
```

### index.md / log.md Templates

```markdown
# Wiki Index
> One line per page under its type. Last updated: YYYY-MM-DD | Pages: N

## Entities
## Concepts
## Comparisons
## Queries
```

```markdown
# Wiki Log
> Append-only. Format: `## [YYYY-MM-DD] action | subject`

## [YYYY-MM-DD] create | Wiki initialized
```

## Operations

### Ingest

1. **Capture the source** into `raw/`: URL/PDF → extract to markdown; pasted text
    → save directly. Name it descriptively (`raw/karpathy-llm-wiki.md`).
2. **Discuss takeaways** with the user (skip in automated contexts).
3. **Check what exists** — search `index.md` and `raw/` neighbors for mentioned
   entities/concepts before creating anything.
4. **Write/update pages** per the SCHEMA thresholds. Cross-link where relationships
   are real. Only use tags from the taxonomy. On conflicts, follow the Update Policy.
5. **Update navigation** — add pages to `index.md`, append to `log.md`.
6. **Report** every created or updated file after the source, affected pages,
   `index.md`, and `log.md` are all saved.

### Query

1. Find relevant pages from `index.md` (search the tree for large wikis).
2. Read them and synthesize an answer citing the pages (for example,
   "Based on [[page-a]]...").
3. Save reusable comparisons or deep dives in `queries/`; answer direct lookups
   without a query page.
4. Append the query to `log.md`; the cited answer is complete when every material
   claim is supported by a read page.

### Lint

Report issues with file paths, grouped by severity:

1. **Broken wikilinks** — `[[links]]` pointing to nonexistent pages.
2. **Orphans** — pages with no inbound links.
3. **Index completeness** — every page appears in `index.md`.
4. **Frontmatter** — required fields present; tags in the taxonomy.
5. **Oversized pages** — over the SCHEMA size threshold, candidates for splitting.
6. **Contradictions** — pages on the same topic stating conflicting facts; surface both for review.
7. **Stale claims** — pages a newer source has superseded but that weren't updated.
8. Append `## [YYYY-MM-DD] lint | N issues found` to `log.md`. The lint is
   complete when every listed check has a result, including zero-issue checks.

## Invariants

- Treat `raw/` as immutable, unless user want to append notes of books.
- **Orient before work.** Read `SCHEMA.md`, `index.md`, and recent `log.md` before
  ingesting, querying, or linting.
