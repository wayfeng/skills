---
name: critical-reading
description: Analyze an article, research paper, or book using the eight elements of reasoning and nine universal intellectual standards. Use when the user asks for critical analysis, evaluation, critique, argument review, paper review, article analysis, or book analysis.
---

# Critical Reading

Analyze the source's reasoning, not whether you agree with its conclusion.

## Framework

Eight elements: purpose, question, information, inference, assumptions,
concepts, implications, and point of view.

Nine standards: clarity, accuracy, precision, relevance, depth, breadth,
logic, significance, and fairness.

## Workflow

1. Establish the source, edition or version, date, author, and source type.
2. State coverage limits. Do not imply whole-book analysis from excerpts.
3. Give the central thesis and argument map in neutral language.
4. Identify the eight elements. Mark absent or indeterminate elements instead
   of inventing them.
5. Evaluate each identified element with only the standards that materially
   apply. Support every criticism with a quotation, page, section, or passage.
6. Steelman the argument before giving the strongest objections and plausible
   alternative explanations.
7. Conclude with what is well supported, what remains uncertain, and what
   evidence would change the assessment.

Keep these distinct:

- `Author states`: explicit in the source.
- `Analysis infers`: a reasonable interpretation, not an explicit statement.
- `Not established`: unsupported or unavailable from the provided material.

Verify externally checkable claims when tools and primary sources are
available. Otherwise label them unverified. Never fabricate citations, page
numbers, quotations, methods, data, or author intent.

## Source-Type Checks

### Article

Check headline-body fit, omitted context, source quality, framing, timeliness,
and whether fact, reporting, and opinion are clearly separated.

### Research Paper

Check research question, study design, sample, measurement, controls,
statistical and practical significance, uncertainty, reproducibility,
limitations, conflicts of interest, and whether conclusions exceed the data.
Do not treat peer review as proof of correctness.

### Book

Check scope, chapter-to-thesis coherence, representative versus cherry-picked
examples, use of sources, treatment of counterarguments, conceptual
consistency, and whether descriptive claims become prescriptive without
justification.

## Output

Use this structure, omitting empty sections:

```markdown
# Critical Analysis: [Title]

## Scope
[Material analyzed and limitations]

## Thesis And Argument
[Neutral thesis, main premises, and conclusion]

## Reasoning Elements
| Element | What the source uses | Assessment |
|---|---|---|

## Quality Evaluation
### Strengths
- [Standard]: [evidence-based finding]

### Weaknesses
- [Standard]: [evidence-based finding and why it matters]

## Steelman And Challenges
[Strongest version, objections, and alternatives]

## Verdict
[Supported, uncertain, unsupported, and evidence needed]
```

Do not assign a numeric score unless the user asks for one. Prefer calibrated
terms such as strong, adequate, weak, unsupported, and indeterminate.
