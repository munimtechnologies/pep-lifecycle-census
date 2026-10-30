# Pre-registration: PEP lifecycle census, follow-up 1 (topic, thresholds, P5 without packaging)

**By MV2 of Munim, Inc. Prepared with AI agents working in his name.**
**Filed: 2026-10-30 (UTC), after run 1 was graded and before this job's statistics were
computed.** Code: Apache-2.0. Text: CC BY 4.0.

## Why

Run 1 (`results/run1-summary.json`) graded five predictions on the 2026-10-30 snapshot of
https://peps.python.org/api/peps.json. Three things it left open:

1. P1 REVERSED: only 9 of 317 accepted Standards Track PEPs are still "Accepted". On the live
   PEP 0 and packaging topic pages, 8 of those 9 have the topic "packaging". That was SEEN
   BEFORE this filing, so F1 below is a confirmation from the index file, not a blind test.
2. P2 HELD by one PEP at a 5-year threshold, so its robustness is unknown.
3. P5 HELD, but packaging PEPs usually have no Python-Version header, which may drive the gap.

## Data

The same index file and data volume as run 1 (data_key peps-json), so the same snapshot.
Topic is a string in the index; it is split on commas and lowercased. A PEP is "packaging"
if one of its topics is "packaging".

## Predictions and rules

**F1 (confirmatory, not blind).** Among Standards Track PEPs with status Accepted or Final,
the Accepted share is above 0.10 for packaging PEPs and below 0.02 for all other PEPs.
HELD if both hold; REVERSED if the packaging share is not above the other share; otherwise
PARTIAL.

**F2 (partly informed: the Deferred list on PEP 0, which shows numbers but not creation
dates, was seen before filing).** The share of all dated PEPs that are Draft or Deferred and were created at
least 10 years (3,652 days) before the snapshot is above 0.03. HELD if above, else REVERSED.
The 4-year share is reported with no prediction.

**F3 (partly informed: the 39 Final packaging PEPs on the packaging topic page were seen,
but not their Python-Version headers).** Repeating P5 with packaging PEPs removed: among non-packaging Standards Track
PEPs, the Final share with a Python-Version header minus the Final share without one is above
0.10. HELD if above 0.10; REVERSED if it is below -0.02; otherwise NULL.

## Outputs

`summary.json` holds the metrics, the verdicts, a topic histogram, the numbers of the
Accepted PEPs in each group, and the numbers of the 5-year aged drafts by status, so every
count can be checked by hand against peps.python.org.

## Limits

One snapshot; topic labels are editor-assigned. None of F1-F3 is fully blind (see above),
so this follow-up is a robustness check on run 1, not a new independent test.
