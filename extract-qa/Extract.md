# Extract Workflow

## 1. Get the Source

Fetch URLs, read local files, and use supplied text directly. Capture the core claim, its support, examples, and boundaries.

**Complete when:** the source evidence needed to answer every question is available.

## 2. Find the Argument Skeleton

Write the core claim in one sentence and its 3-5 critical reasoning turns. Re-read the source until the chain is supported.

**Complete when:** each turn supports or qualifies the claim.

## 3. Design the Chain

Draft questions from the critical turns, ordered by reasoning dependency. Apply [QuestionDesign.md](QuestionDesign.md).

**Complete when:** the draft has 5-10 questions that cover the argument without paraphrasing it.

## 4. Write Answers

Write each answer using the four-part structure in [QuestionDesign.md](QuestionDesign.md).

**Complete when:** every answer is grounded in the source and closes with a real boundary.

## 5. Check Direction

Read the questions in order. Reorder or merge parallel questions until each one creates the need for the next.

**Complete when:** removing a key question weakens a later one.

## 6. Redline

Run the self-check in [QuestionDesign.md](QuestionDesign.md) and revise every failed item.

**Complete when:** every self-check item passes.

## 7. Write the File

Write `qa/{YYYYMMDD}-{topic}.md`, with a 5-10 word, punctuation-free English topic. Include frontmatter (`title`, `subtitle`, `date`, `tags`, `identifier`, `source`), a 3-5 sentence `Hook`, `Q1...Qn`, and a one-sentence `Closure`. Report the full path.

**Complete when:** the Markdown file has the required shape and passes the self-check.
