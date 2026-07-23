---
name: storm-research
description: Write a long-form, cited research report on a topic using the STORM method — discover multiple perspectives, simulate grounded expert Q&A to mine good questions, then outline, draft with citations, and polish. Co-STORM mode adds interactive turn-by-turn steering with a moderator and a mind map. Use when the user says "deep research", "research report", "write an article/report on X", "literature-style writeup", "multi-perspective research", "STORM", or "Co-STORM". Do NOT use for quick factual lookups (just answer) or single-source summaries (use a plain summary).
---

Turn a bare topic into a researched, cited report. The bottleneck is asking
**good questions**; get them from (1) multiple perspectives and (2) grounded
expert Q&A. Retrieval = `WebSearch`/`WebFetch`. Perspectives/experts = parallel
subagents. Default to STORM mode; switch to Co-STORM when the user wants to steer.

## Mode 1 — STORM (automated, default)

1. **Perspectives** — derive 3–5 *distinct* angles on the topic (e.g. do a
   quick search for how similar articles are structured, then name the facets:
   historical, technical, economic, critical, stakeholder-specific…). List them
   back to the user before fanning out.
2. **Simulated Q&A research** — spawn one subagent per perspective, **all in a
   single message** (parallel). Each agent runs a short writer↔expert loop:
   ask a question from its perspective → `WebSearch`/`WebFetch` to ground the
   answer → ask a grounded follow-up (2–4 rounds). It returns
   source-attributed notes: `claim — URL`.
3. **Outline** — merge all notes into one hierarchical outline. Dedupe where
   perspectives overlap; drop unsupported threads.
4. **Write** — draft section by section from the outline + collected snippets.
   Inline-cite every non-trivial claim as `[n]`, mapped to a numbered source
   list at the end.
5. **Polish** — add a lead/summary section, cut duplication, and verify every
   `[n]` resolves to a listed source and every claim traces to one.

## Mode 2 — Co-STORM (interactive, when the user wants to steer)

Run a turn-based discourse instead of one shot.

- **Each step** — an expert subagent contributes one grounded answer or
  follow-up question. Every few turns, play a **moderator** move: inject a
  question drawn from retrieved-but-unused material (the *unknown unknowns*),
  not from what's already been said.
- **Mind map** — maintain a nested-bullet concept tree of what's been learned;
  show it as shared state and update it each turn so a long inquiry stays legible.
- **User control** — the user either *observes* (say "next"/"step" to advance a
  turn) or *injects* an utterance to steer focus. Honor injections immediately.
- **Report** — on request, reorganize the mind map into an outline and run the
  Write + Polish stages from STORM mode.

## Shared rules

- Every non-trivial claim carries a citation; keep one running numbered source list.
- Prefer breadth of *distinct* sources over re-reading one.
- Always parallelize perspective/expert subagents in a single message.
- Scale effort to the ask: a quick brief = fewer perspectives and turns; a deep
  report = more. Don't fan out 5 agents for a one-paragraph answer.
- State it plainly when a claim couldn't be grounded — don't paper over gaps.
