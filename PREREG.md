# Pre-registration: PEP lifecycle census

**By MV2 of Munim, Inc. Prepared with AI agents working in his name.**
**Pre-registered: 2026-10-29 (UTC), before any statistic below was computed.**
Field: Discoveries. This document fixes the hypotheses and decision rules
*before* the data are analysed. Results, when the verifier runs, go in
`summary.json`; this file is not edited afterward except to link the result.

Re-filed 2026-10-30 as pep-lifecycle-census-v2: the v1 job never started
(jobs filed after it ran and finished), so it was re-filed with network access
for the download and a file-name fallback in `load_peps`. Hypotheses, decision
rules and metric code are unchanged; still no statistic has been computed.

## Data

Single public file: the authoritative Python Enhancement Proposal index,
`https://peps.python.org/api/peps.json` (~432 KB JSON, one object per PEP).
Fields used, all raw in the file: `number`, `status`, `type`, `topic`,
`created` (format `dd-mmm-yyyy`), `python_version`, `author_names` (list),
`resolution`, `superseded_by`, `replaces`. No other data source.

The analysis snapshot date is the date the verifier downloads the file; it
is recorded in `summary.json` as `snapshot_date`. Ages are measured from
`created` to `snapshot_date`.

## Status taxonomy (from PEP 1)

- OPEN = {Draft, Deferred, Provisional} -- not finally resolved.
- ACCEPTED_LIMBO = {Accepted} -- proposal accepted, implementation not yet
  marked complete (the "Accepted but not Final" state discussed on
  discuss.python.org, "Multiple released PEPs have status Accepted, not Final").
- FINAL = {Final}.
- NEGATIVE = {Rejected, Withdrawn, Superseded}.
- ACTIVE = {Active} -- normative, continually updated (mostly Process/Informational).

Only PEP entries actually present in the file are counted; reserved/missing
numbers (numbering gaps) are ignored. PEPs with an unparseable or missing
`created` are excluded only from age-based measures (P2), and that excluded
count is reported.

## Pre-registered claims

Each claim states a direction and a decision rule. A directional claim is
graded HELD, REVERSED, or NULL (NULL when the two quantities differ by less
than the stated epsilon). P1 is descriptive with a pre-registered threshold.

**P1 (headline, descriptive): the "Accepted-not-Final" limbo is substantial.**
Among Standards Track PEPs whose proposal was accepted (status in {Accepted,
Final}), the share still in status `Accepted` (not advanced to `Final`) is
**greater than 10%**. Rationale: the status only flips to Final when the
reference implementation is complete and merged, and nobody routinely goes
back to flip it; the phenomenon is known qualitatively but has never been
counted across the whole corpus. Graded: HELD if share > 0.10, else REVERSED.

**P2 (directional): abandoned drafts ("zombies") are non-trivial.**
Among all PEPs with a parseable `created` date, the share that are still in
status Draft or Deferred *and* were created at least 5 years before the
snapshot is **greater than 5%**. Rationale: proposals stall and are rarely
formally rejected, leaving effectively-dead drafts on the books. Graded:
HELD if share > 0.05, else REVERSED.

**P3 (directional): Standards Track PEPs are rejected/withdrawn more than
Process PEPs.** NEGATIVE-share of Standards Track > NEGATIVE-share of Process,
where NEGATIVE-share(type) = |type PEPs in NEGATIVE| / |type PEPs|.
Rationale: technical proposals compete and face more scrutiny than process
PEPs. Graded: HELD if ST_share - Process_share > 0.02; REVERSED if
Process_share - ST_share > 0.02; else NULL.

**P4 (directional): successful PEPs have more authors.**
Median `len(author_names)` for status == Final is greater than the median
for status in {Rejected, Withdrawn}. Rationale: more backing -> more likely
to be carried to completion. Graded: HELD if median(Final) > median(Rej/Wd);
REVERSED if <; NULL if equal.

**P5 (directional): a target version predicts success.**
Among Standards Track PEPs, the Final-share of those WITH a non-null
`python_version` exceeds the Final-share of those WITHOUT one.
Final-share(group) = |group with status Final| / |group|. Rationale: a
concrete target release signals committed, scheduled implementation.
Graded: HELD if with_version - without_version > 0.02; REVERSED if the
reverse > 0.02; else NULL.

## What a reversal would mean (the valuable shapes)

- P1 REVERSED: the "Accepted limbo" is a myth; editors keep status current.
- P3 REVERSED: process PEPs are *more* contested than technical ones.
- P4 REVERSED: lone-author PEPs succeed as often as multi-author ones --
  evidence that authorship breadth is not a success signal.
- P5 REVERSED: tagging a target version does not track completion.
Per the field's methodology, a clean reversal with a mechanistic reading is
the most valuable write-up shape; a NULL honestly reported also counts.

## Novelty and nearest prior art (delta stated)

- Noah Gorstein, "Exploring PEPs with Python and Graphs" -- a status *pie
  chart* and an author collaboration graph; no lifecycle, terminality,
  cohort or association statistics. Delta: this study measures outcome
  structure and associations, not just a status breakdown.
- "Drafts That Never Shipped" (dev.to, Hassan Shah) -- an *LLM-behaviour
  benchmark* over 122 hand-picked entities (incl. deferred PEPs like 505,
  3150); tests whether models treat dead proposals as real. It is not a
  statistical census of the PEP corpus. Delta: this study is about the
  corpus's own lifecycle, not model behaviour.
- A ResearchGate figure on the PEP *process* (state-machine with ~13 states,
  52 of 78 pairwise transitions observed) -- qualitative transition mining,
  not pre-registered quantities. Delta: fixed hypotheses + decision rules.

No published work quantifies, with pre-registered predictions, the
Accepted-not-Final share (P1), the aged-draft share (P2), or the
type/author/version associations with outcome (P3-P5) across the full
corpus. That is the contribution.

## Limits (stated up front)

- `resolution` is a URL, not a date, so this file alone cannot give
  time-to-resolution; all timing here uses `created` -> snapshot age only.
- Status is an editor-maintained convention, not ground truth; the verifier
  records the live status of 6 named PEPs so they can be spot-checked.
- Right-censoring: recent PEPs have had less time to resolve; P2 is designed
  around this (it *measures* long-pending drafts rather than assuming
  everything resolves), and per-type shares (P3, P5) are reported with their
  denominators so the reader can judge.
- This is a property of the PEP corpus at one snapshot, not a law of
  software governance.
