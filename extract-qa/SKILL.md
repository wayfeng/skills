---
name: extract-qa
description: Extract a source's reasoning into a directional Q-A chain. Use for articles, papers, books, URLs, PDFs, or supplied text; questions expose mechanism, trade-offs, and boundaries.
---

# Extract Q-A

Turn one source into a directional Q-A chain that reconstructs its argument.

## Contract

- Ask 5-10 questions that follow reasoning dependency rather than source order.
- Make every question answerable from the source and resistant to a one-line definition.
- Give every answer a standalone conclusion, a one-line formalization, reasoning steps, and a boundary.

**Complete when:** removing a key question weakens later questions, and every answer has all four parts.

## Workflow

For source handling, extraction, output shape, and acceptance, follow [Extract.md](Extract.md).

## Design Reference

For question types, answer structure, and the final self-check, follow [QuestionDesign.md](QuestionDesign.md).
