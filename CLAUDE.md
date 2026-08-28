# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of **agent skills** — one skill per top-level directory, each defined by a `SKILL.md`. There is no build, lint, or test system; the deliverables are the markdown files themselves (prompt/behavior specs consumed by Claude Code or other LLM agents). "Testing" a skill means reading it as an agent would and checking the instructions are unambiguous and self-consistent.

## Skill anatomy

Every skill directory contains a `SKILL.md` starting with YAML frontmatter:

```yaml
---
name: <kebab-case-name>          # how the skill is invoked; may differ from dir name
description: <one line>          # when-to-use trigger, often includes explicit "do not use for..."
---
```

Note `name` in frontmatter is authoritative and can diverge from the folder name (e.g. `onnx_model/` → `name: model-convert-and-benchmark`). Descriptions are written as activation triggers with negative cases ("Do not use for...") — preserve that style when editing.

A skill may bundle supporting files the SKILL.md references:
- `extract-qa/` splits detail into `Extract.md` + `QuestionDesign.md` alongside `SKILL.md`.
- `onnx_model/` ships `setup_remote_ssh.sh`, invoked from the workflow steps.

## Existing skills

- `coding_guidelines/` — behavioral rules to curb LLM coding mistakes (Karpathy-derived).
- `extract-qa/` — turn a source into a why→how→boundary Q-A chain.
- `llm-wiki/` — build/query an interlinked markdown knowledge base (Karpathy's LLM Wiki pattern; path via `WIKI_PATH`, default `~/wiki`).
- `onnx_model/` — reproducible PyTorch→ONNX→OpenVINO convert + remote benchmark pipeline.
- `vocabulary/` — English vocabulary activation coach (authored in Chinese).

## Conventions

- Skills are written in the language of their target user — `vocabulary` and parts of others are in Chinese; match the existing language when editing a given skill.
- Keep instructional prose terse and imperative; these are read by agents, not humans browsing docs.
- `onnx_model` assumes CPU torch wheels, an Intel/OpenVINO toolchain, and Intel-internal infra (proxy `child-prc.intel.com`, `rtk`, remote `benchmark_app`) — those specifics are intentional, not placeholders.
