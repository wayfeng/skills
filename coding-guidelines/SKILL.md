---
name: coding-guidelines
description: Surgical coding rules for implementation, bug fixes, refactors, and reviews. Use to resolve ambiguity, limit scope, and leave a checkable result.
license: MIT
---

# Coding Guidelines

## 1. Resolve

Read the affected code and its callers before choosing an approach. State an assumption or ask one focused question when the request has materially different outcomes.

**Complete when:** the requested behavior and the smallest viable approach are explicit.

## 2. Change

Make the smallest change that delivers the requested behavior. Reuse local patterns and remove only artifacts created by the change. Keep unrelated code and formatting intact.

**Complete when:** every changed line traces to the request and the surrounding style remains consistent.

## 3. Verify

Define a check that would fail without the change, then run the narrowest available check. For a bug, make the failure reproducible before confirming the fix; for a refactor, preserve existing behavior.

**Complete when:** the relevant check passes, or its absence and the manual evidence are reported.
