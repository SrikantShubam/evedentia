# Evidentia Frontend Input Validation Tests

Last updated: 2026-04-15
Scope: user-input tests for the live frontend at `https://evidentia-srikantshubams-projects.vercel.app`

## Purpose

This file is not for domain coverage.

This is only for the user flow:
1. user enters an input
2. frontend sends the request
3. frontend shows validation-style output
4. the output reflects semantic clustering and synthesized hypotheses instead of raw item spam
5. you paste the output back to me
6. I validate whether the behavior is correct

## What to paste back to me

For every test, send:

```text
TEST ID: <id>
INPUT:
<exact text you entered>

OUTPUT:
<paste the visible UI output verbatim>
```

Paste exactly what the UI shows:
- error text
- source badges
- cluster labels
- synthesized hypothesis text
- keep / revise / kill text
- verdict text
- score text
- quote text
- discard text
- spec text

Do not summarize.

## What counts as correct output

I am validating structure first, not whether the internet returns the same signals every time.

For scan results, the output is acceptable if it includes some or all of:
- source attempt badges such as `hn: 2 hits`
- one or more cluster-synthesized hypothesis cards
- a verdict like `PURSUE`, `HOLD`, or `DISCOVER`
- a score
- a cluster summary or synthesis label
- one or more quotes with source URLs
- a discard section
- a prosecutor or validation note such as `keep`, `revise`, or `kill`

For empty or failing runs, the output is acceptable if it includes:
- `error: ...`
- or `no synthesized hypotheses returned -- all candidates were KEEP/REVISE/KILL or discarded`

For spec generation, the output is acceptable if it includes:
- title
- opportunity id
- cluster id or cluster summary
- `TARGET USER`
- `CORE PROBLEM`
- `WEDGE FEATURE`
- synthesized hypothesis summary
- validation state
- `SOURCES (n)`
- `approved: false -- review the spec and set approved: true before deploying`

## Test 1: Empty input guard

Test ID: `INPUT-001`

User input:
- leave the input box empty

Action:
- click `scan ->`

Paste back:
- whether the button was clickable or disabled
- whether any UI output appeared

## Test 2: Input echo label

Test ID: `INPUT-002`

User input:

```text
invoice reconciliation
```

Action:
- type the input
- do not scan yet

Paste back:
- the exact label shown above `Try it now.`

Correct pattern:

```text
Evidentia + invoice reconciliation
```

## Test 3: Basic scan run

Test ID: `INPUT-003`

User input:

```text
invoice reconciliation
```

Action:
- keep default source selection
- keep default max results
- click `scan ->`

Paste back:
- all source badges
- the first synthesized hypothesis card, if present
- the cluster summary, if present
- or the empty-state message
- or the error banner

## Test 4: Different input phrase

Test ID: `INPUT-004`

User input:

```text
expense tracking for small teams
```

Action:
- keep default source selection
- click `scan ->`

Paste back:
- all source badges
- the first synthesized hypothesis card, if present
- the cluster summary, if present
- or the empty-state message
- or the error banner

## Test 5: Very short input

Test ID: `INPUT-005`

User input:

```text
crm
```

Action:
- keep default source selection
- click `scan ->`

Paste back:
- all source badges
- the first synthesized hypothesis card, if present
- the cluster summary, if present
- or the empty-state message
- or the error banner

## Test 6: Long natural-language input

Test ID: `INPUT-006`

User input:

```text
teams struggling to collect invoices and follow up on overdue payments
```

Action:
- keep default source selection
- click `scan ->`

Paste back:
- all source badges
- the first synthesized hypothesis card, if present
- the cluster summary, if present
- or the empty-state message
- or the error banner

## Test 7: Enter-key submit

Test ID: `INPUT-007`

User input:

```text
b2b invoicing
```

Action:
- keep default source selection
- press `Enter` inside the text field instead of clicking the button

Paste back:
- whether loading started
- all source badges
- any visible result block or error block

## Test 8: Empty-results behavior

Test ID: `INPUT-008`

User input:

```text
zzzxxyyq invalid niche
```

Action:
- keep default source selection
- click `scan ->`

Paste back:
- the exact result message
- all source badges
- any error banner

Possible valid output:

```text
 no synthesized hypotheses returned -- all candidates were KEEP/REVISE/KILL or discarded
```

## Test 9: Error-state capture

Test ID: `INPUT-009`

User input:

```text
invoice automation
```

Action:
- run this only if the backend is currently failing or unavailable
- click `scan ->`

Paste back:
- the full red error line

Expected pattern:

```text
error: <message>
```

## Test 10: Spec generation from result

Test ID: `INPUT-010`

Precondition:
- first get at least one visible synthesized hypothesis card from any previous test

Action:
- click the spec-generation action on the first hypothesis

Paste back:
- spec title
- opportunity id
- cluster id
- `TARGET USER`
- `CORE PROBLEM`
- `WEDGE FEATURE`
- synthesized hypothesis summary
- validation state
- `SOURCES (n)`
- the final approval warning line

Required warning line:

```text
approved: false -- review the spec and set approved: true before deploying
```

## Fastest set to run

If you want the minimum useful set, run only:
- `INPUT-001`
- `INPUT-002`
- `INPUT-003`
- `INPUT-003`
- `INPUT-008`
- `INPUT-010`
