---
name: storm-research
description: Research a topic into a cited long-form report using STORM, or run an interactive Co-STORM inquiry with expert turns and a mind map. Use for deep, multi-perspective research; use Co-STORM when the user wants to steer the inquiry.
---

Turn a topic into a cited report. Default to STORM; use Co-STORM when the user
wants turn-by-turn control.

## STORM

1. **Perspectives** — identify 3-5 distinct research angles and show them to
   the user. Complete when each angle covers a different question the report
   must answer.
2. **Research** — dispatch one subagent per angle in parallel. Each runs 2-4
   grounded writer-expert Q&A rounds and returns notes as `claim — URL`.
   Complete when every retained note has a source.
3. **Outline** — merge the supported notes into a hierarchical outline.
   Complete when each section has supporting notes and overlaps are removed.
4. **Draft** — write the requested report from the outline. Cite each
   non-trivial claim as `[n]`.
5. **Polish** — add the lead, remove duplication, and check that every citation
   resolves to a numbered source and supports its claim.

## Co-STORM

Run one expert turn at a time. Maintain and show an updated nested-bullet mind
map after each turn. Accept `next`/`step` to advance, or apply the user's
steering immediately. Every few turns, introduce a moderator question from
sourced material not yet discussed. On request, turn the mind map into the
STORM outline, draft, and polish stages.

## Research rules

- Use available retrieval tools and provide source URLs.
- Use the fewest perspectives and Q&A rounds that support the requested scope.
- State unsupported gaps plainly.
