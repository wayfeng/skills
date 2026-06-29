---
name: extract-qa
description: Q-A extraction engine. Turn an article/paper/book into a sharp question chain plus compact answers. Questions target mechanism, trade-offs, and limits; answers stay structured and concrete. Do not use for FAQ, glossary, or quiz generation.
---

# extract-qa: Q-A Extraction

Read a source and turn its ideas into a "why -> how -> boundary" Q-A chain.

Each question moves the argument forward. Each answer locks one key point in place.

## You are not

- Not an FAQ generator ("What is X?").
- Not a summary in disguise (paragraph split into Q/A).
- Not a loose fact list.
- Not a comprehension quiz.

## You are

Expose the author's reasoning skeleton. Turn each major hinge into a sharp question. The reader should be able to recreate the full argument by following the chain.

## Three rules

1. *Questions must cut to the core* - ask why it works, why this over alternatives, what it costs, and where it breaks. Avoid definition-only questions.

2. *Answers must have structured closure* - each answer has four parts: *Conclusion* (one line), *Formalization* (one visual relation line, e.g. `A = B + C`, `old: X -> new: Y`), *Reasoning Steps*, and *Boundary* (where it does not hold).

3. *The question chain must have direction* - Q2 should naturally emerge after Q1 is answered. The full chain should mirror the argument path.

## Workflow

Follow `Workflows/Extract.md`.

## Design Reference

For question patterns and answer closure patterns, see `QuestionDesign.md`.

## Output

- Format: html
- Denote filename: `{YYYYMMDD}--{core-topic-5-10-words}.html`

## Examples

*Example 1: URL*

```
User: /extract-qa https://example.com/article
-> Fetch with WebFetch
-> Find the argument skeleton -> design Q chain -> write A blocks
-> Output html to $PWD
```

*Example 2: Paper PDF*

```
User: /extract-qa ~/Downloads/paper.pdf
-> Read PDF (use page slicing for large files)
-> Build Q around why, trade-offs, and boundaries
-> Output html to $PWD
```

*Example 3: Raw Text*

```
User: Turn this into Q-A: [text]
-> Skip fetching
-> Extract and output
```

## Gotchas

- *Default drift to "What is X" questions* - rewrite any question that can be answered by a one-line definition.
- *Default drift to loose answers* - every A must keep all four parts: conclusion, formalization, steps, boundary.
- *Formalization is not math-heavy notation* - use short text + simple symbols for visible relations.
- *Do not follow chapter order blindly* - order by dependency in reasoning.
- *This is not a Q-A game* - questions are chisels; answers are load-bearing.
- *Do not hide behind jargon* - convert terms into concrete actions or objects.
