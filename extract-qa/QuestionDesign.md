# Question Design

How to make questions sharp and answers tight.

## Four Question Types (Action / Contrast / Causality / Boundary)

Each type anchors one part of the argument. A strong chain mixes at least three.

| Type | Pattern | Example |
|------|---------|---------|
| *Action* | "How is it done?" | "How does it turn X into Y?" |
| *Contrast* | "Why A, not B?" | "Why iterate instead of parallelize?" |
| *Causality* | "Why does it work?" | "Why does chain reasoning emerge?" |
| *Boundary* | "When does it fail?" | "Does this still hold under sparse data?" |

Why mixing matters:

- Action-only -> tutorial
- Contrast-only -> debate
- Causality-only -> theory paper
- Boundary-only -> critique

Mixing them recovers real tension: method + cost + limits.

## Question Anti-Patterns

- `What is X?` -> definition-level, no load
- `How many steps does X have?` -> asks for table of contents
- `Is X important?` -> low tension
- `How should we view X?` -> abstract, no action
- `What are pros and cons of X?` -> generic template
- `What does X mean for the future?` -> hard to ground

## Question Tone

Do not pad. Ask directly.

| Before | After |
|--------|-------|
| How should we think about token efficiency? | Where does token spend actually pay off? |
| Is parallel processing suitable in AI engineering? | Why does shotgun parallelism fail? |
| What is the core mechanism of this method? | Why can this method work at all? |
| What are the limitations of this method? | Where does it break? |

Prefer spoken clarity over academic style. Prefer <= 20 words.

## Four-Part Answer Structure

```text
*Conclusion*: one sentence, standalone
*Formalization*: one visual relation line
*Reasoning Steps*: 2-4 short inference steps
*Boundary*: where it does not hold / what it does not cover
```

### Conclusion Requirements

The line should still make sense out of context.

- Good: `Depth is costlier than breadth, but only depth buys insight.`
- Good: `Reward signals can trap a model in already-known trajectories.`
- Weak: `Overall, token use should be more careful.`
- Weak: `This method shows advantages across multiple dimensions.`

### Formalization Requirements

Compress the idea into one visual relation line using words + simple symbols.
This is the geometry of thought, not heavy math notation.

Allowed symbols: `= != -> <- + - x / < > and or` with plain text.
Avoid LaTeX and complex notation.

Common patterns:

| Pattern | Example | Best use |
|------|------|------|
| *Equation* | `generalist = coordinator; specialist = executor` | Assign roles |
| *Contrast* | `old: model = full-stack -> new: model = coordinator` | Flip default frame |
| *Flow* | `data -> tokens -> answer = loss + waste` | Show pipeline loss |
| *Progression* | `call -> interface -> bilingual hotline` | Trace root cause |

Also valid as a very short formula or ASCII sketch:

```text
depth = 1 agent x 100 steps > 100 agents x 1 step
```

or

```text
breadth: ---- ---- ---- (shallow)
depth:   |
         v (drill)
```

Test: if someone reads only this line, can they get the rough idea? If not, rewrite.

### Reasoning Step Requirements

Each bullet should express one inference only. Steps must unlock each other.

Good:

- 100 agents think 1 step each; hit rate is about 1/50
- 1 agent thinks 100 steps; each output becomes next input
- Same token budget, different hit rates

Bad:

- In multi-agent settings, increasing parallel workers does not necessarily improve quality because quality is tightly related to reasoning depth, and depth requires iterative time...

If one bullet contains everything, the chain is not traceable.

### Boundary Requirements

Boundary is an honesty check. Every claim has failure conditions.

- Good: `Assumes the target is stable and repeatedly verifiable; open-ended tasks (e.g., poem writing) may not benefit from depth-first reasoning.`
- Good: `May not hold for small models where iterative gain saturates quickly.`
- Weak: `(no boundary)`
- Weak: `Future work can explore more dimensions.`

Boundary is not a "drawback" list. Boundary states conditions.

## Q-A Chain Topology

This is a path, not a list. Sketch dependencies first:

```text
Q1 --+--> Q2 (deepen Q1 answer)
    +--> Q3 (contrast raised by Q1)
Q2 ----> Q4 (triggered by Q2 boundary)
Q4 ----> Q5 (closing turn)
```

If readers can move from Q1 to Q5 and recover the argument, topology is working.

Flat ordering = FAQ. Dependency ordering = reasoning path.

## Quantity Control

Sweet spot: 5-10 questions.

- <5: under-covered
- >10: reader fatigue
- 7 +/- 2 is usually best

If source density is high (book chapter or deep paper), split into multiple themed Q-A files, each with 5-10 questions.

## Self-Check

Before final output, verify:

- [ ] Every Q resists one-line definition answers
- [ ] Every A has all four parts
- [ ] Conclusion line works out of context
- [ ] Formalization line is legible by itself
- [ ] Reasoning steps are one-inference-per-line
- [ ] Boundary states failure conditions, not "future work"
- [ ] Chain has direction (remove one Q and later Qs weaken)
- [ ] At least three question types are used
- [ ] No `What is X` questions
- [ ] Each Q <= 20 words
- [ ] Total count is 5-10
- [ ] Plain natural English, no academic filler

If any item fails, revise.
