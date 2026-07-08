---
name: llm-wiki
description: "Karpathy's LLM Wiki: build/query interlinked markdown knowledge base."
---

# Karpathy's LLM Wiki

Build and maintain a persistent knowledge base as interlinked markdown files.
Based on [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

Unlike RAG (which rediscovers knowledge per query), the wiki compiles knowledge
once and keeps it current. Cross-references and synthesis are already there.

**Division of labor:** The human curates sources and directs analysis. The agent
summarizes, cross-references, files, and keeps things consistent.

## When This Activates

- User asks to create/build a wiki or knowledge base
- User asks to ingest a source into their wiki
- User asks a question and a wiki exists at the configured path
- User asks to lint/audit their wiki

## Location

Set via `WIKI_PATH` env var; defaults to `~/wiki`.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

It's just a directory of markdown — open it in Obsidian, VS Code, or any editor.
No database, no special tooling. The directory works as an Obsidian vault out of
the box: `[[wikilinks]]` render as links, frontmatter powers Dataview, Graph View
visualizes the network.

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

## Orient Before Acting (every session on an existing wiki)

1. Read `SCHEMA.md` — domain, conventions, tags.
2. Read `index.md` — what pages exist.
3. Skim recent `log.md` — recent activity.

Only then ingest/query/lint. This prevents duplicate pages and missed links.

## Initialize a New Wiki

1. Determine the path (`$WIKI_PATH`, or ask; default `~/wiki`).
2. Create the directory structure above.
3. Ask what domain the wiki covers.
4. Write `SCHEMA.md` (template below), `index.md`, and `log.md`.
5. Suggest first sources to ingest.

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
- Don't create pages for passing mentions
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
6. **Report** every file created or updated.

A single source can touch 5-15 pages. That's the compounding effect.

### Query

1. Read `index.md` to find relevant pages (search the tree for large wikis).
2. Read the pages, synthesize a cited answer ("Based on [[page-a]]...").
3. File substantial answers (comparisons, deep dives) into `queries/`. Skip trivial lookups.
4. Log the query.

### Lint

Report issues with file paths, grouped by severity:

1. **Broken wikilinks** — `[[links]]` pointing to nonexistent pages.
2. **Orphans** — pages with no inbound links.
3. **Index completeness** — every page appears in `index.md`.
4. **Frontmatter** — required fields present; tags in the taxonomy.
5. **Oversized pages** — over the SCHEMA size threshold, candidates for splitting.
6. **Contradictions** — pages on the same topic stating conflicting facts; surface both for review.
7. **Stale claims** — pages a newer source has superseded but that weren't updated.
8. Append `## [YYYY-MM-DD] lint | N issues found` to `log.md`.

## Two things that break the wiki

- **Never modify `raw/`** — sources are immutable; corrections go in wiki pages.
- **Never skip orienting** — reading `SCHEMA.md`/`index.md`/`log.md` first is what prevents duplicate pages and missed links.
