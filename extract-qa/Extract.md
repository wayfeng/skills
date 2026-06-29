# Extract Workflow

Turn one source into a directional Q-A chain.

## Step 1: Get the Source

Choose by input type:

| Input | Tool | Notes |
|------|------|------|
| URL (web page) | WebFetch | Use markdown-proxy if login is required |
| arXiv link | WebFetch (HTML) | Capture abstract + method + experiment sections |
| PDF / local file | Read | For large PDFs, read by page chunks |
| Raw text | Skip | Go straight to Step 2 |
| Paper/book title | WebSearch | Find URL first, then WebFetch |

Make sure you capture: core claim, argument chain, key examples, and boundary discussion.

## Step 2: Find the Argument Skeleton

After reading, pause briefly and answer:

> What is the central claim? How is it supported? Which turns are critical?

Write:

- *Core claim*: one sentence
- *3-5 key turns*: one sentence each

This is the spine of your Q chain. If it is weak, re-read before continuing.

## Step 3: Design the Q Chain

Each key turn should generate one or more questions. Every question must:

1. Resist one-line definition answers
2. Be answerable from the source
3. Inherit from the previous question (Q2 should emerge after Q1)

Question types (Action / Contrast / Causality / Boundary) are defined in `QuestionDesign.md`.
A good chain mixes at least three types.

*Ordering rule*: order by dependency in reasoning, not chapter order.

*Count*: 5-10 questions. Fewer is thin; more is tiring.

## Step 4: Write Answers

Each answer must have exactly four parts:

```text
*Conclusion*: one sentence, standalone

*Formalization*: one visual relation line with words + simple symbols

*Reasoning Steps*:
- Step 1 (single inference)
- Step 2
- Step 3

*Boundary*: when the conclusion does not hold
```

Hard requirements:

- *Conclusion*: should still work if copied out of context
- *Formalization*: use words + simple symbols (`->`, `=`, `!=`, `+`, `x`, etc.); show relation at a glance
- *Reasoning Steps*: one inference per bullet; each step opens the next
- *Boundary*: state failure conditions, not "future work"

### Formalization Patterns

Common patterns:

- *Equation*: `generalist = coordinator; specialist = executor`
- *Contrast*: `old: model = full-stack -> new: model = coordinator`
- *Flow*: `data -> tokens -> answer = loss + waste`
- *Progression*: `call -> interface -> bilingual hotline`

Use one line only. Keep it simple and readable.

## Step 5: Check Chain Direction

Read questions in order:

- *Inheritance*: does Q2 naturally follow from Q1?
- *Dependency*: if Q3 is removed, does Q4 still stand?

If questions are parallel and independent, reorder or merge.

Optional scratch graph (do not include in final markdown file):

```text
Q1 --+--> Q2
    +--> Q3
Q2 ----> Q4
Q4 ----> Q5 (closing turn)
```

## Step 6: Redline Checklist

Check line by line:

- [ ] Every Q resists one-line definition answers
- [ ] Every A has all four parts
- [ ] Formalization line is immediately legible
- [ ] Q chain has direction, not a flat list
- [ ] No "What is X" questions
- [ ] Each Q <= 20 words
- [ ] No academic filler tone
- [ ] No jargon-only answers; terms are grounded in concrete actions/objects
- [ ] Total question count is 5-10

If any item fails, revise.

## Step 7: Write the File

Get timestamp:

```bash
date +%Y%m%dT%H%M%S
```

Denote filename schema: `{YYYYMMDD}-{topic}.md`

- Topic is a 5-10 word core claim phrase in English without punctuation

Output path: `$(pwd)/qa`

After writing, report the full path to the user.

## File Shape

Write a markdown file with this structure:

- Frontmatter: `title`, `subtitle`, `date`, `tags`, `identifier`, `source`
- `Hook` section (3-5 sentences: what this source argues and why it is worth questioning)
- `Q1...Qn` sections (`n` in 5-10)
- In each Q section: `Conclusion`, `Formalization`, `Reasoning Steps`, `Boundary`
- `Closure` section (one sentence naming the source's true contribution)

## Acceptance

- *Questions cut to the core*: no definition-only questions
- *Answers close formally*: all four parts present; relation line is clear
- *Chain has direction*: remove one key Q and later steps should weaken
- *Not paraphrase*: rebuild argument skeleton, do not rewrite paragraphs
- *Natural English*: short, direct, concrete language
