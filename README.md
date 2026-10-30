# pep-lifecycle-census

A pre-registered census of the outcomes of all 747 Python Enhancement Proposals (PEPs),
computed from the official index at https://peps.python.org/api/peps.json.

By MV2 of Munim, Inc. (mv2@munimtech.com). The work was made with AI agents working in his
name. Code: Apache-2.0. Results and text: CC BY 4.0.

## What was pre-registered

`PREREG.md` lists five predictions and how each would be graded. It was written on
2026-10-29, before any statistic was computed. `job.py` computes the statistics and
`test_job.py` checks the arithmetic against a hand-built fixture. The job ran once, in a
sealed container, on the index snapshot of 2026-10-30. Its raw output is
`results/run1-summary.json`.

## Results (snapshot 2026-10-30, 747 PEPs)

| | Prediction | Measured | Verdict |
|---|---|---|---|
| P1 | Over 10% of accepted Standards Track PEPs are still "Accepted", not "Final" | 9 of 317 (2.8%) | **REVERSED** |
| P2 | Over 5% of all PEPs are Draft/Deferred and at least 5 years old | 38 of 747 (5.09%) | HELD (barely: 37 would have reversed it) |
| P3 | Standards Track PEPs end Rejected/Withdrawn/Superseded more often than Process PEPs (by more than 2 points) | 31.6% (186 of 588) vs 30.2% (16 of 53) | NULL |
| P4 | Final PEPs have more authors than Rejected/Withdrawn ones (median) | median 1 vs 1 | NULL |
| P5 | Standards Track PEPs with a Python-Version header end Final more often than those without | 56.3% (273 of 485) vs 34.0% (35 of 103) | HELD |

Status counts: Final 375, Rejected 132, Withdrawn 74, Draft 56, Active 38, Deferred 35,
Superseded 25, Accepted 11, Provisional 1. Types: Standards Track 588, Informational 106,
Process 53.

The six spot-check PEPs recorded by the job match the live index: PEP 8 Active, 484 Final,
505 Deferred, 563 Superseded, 649 Final, 3150 Deferred.

## The reversal (P1): the "Accepted but not Final" backlog is gone, except in packaging

The prediction came from a 2022 discussion, "Multiple released PEPs have status Accepted,
not Final" (discuss.python.org topic 20776). The backlog it describes was real, but it has
since been cleared in cleanup campaigns:

- python/peps issue #2872 (opened November 2022, closed June 2024) listed 10 implemented
  PEPs to mark Final, and they were.
- python/peps pull request #4986 (merged 2026-06-15) moved another batch of core and
  packaging PEPs from Accepted to Final.

Of the 9 Standards Track PEPs still "Accepted" on 2026-10-30, 8 carry the topic
"packaging" on the live index (PEPs 458, 658, 714, 739, 752, 783, 794, 808). The ninth,
PEP 828, was accepted on 2026-08-03 and targets Python 3.16, which has not been released,
so it is not overdue. In the review of #4986, a packaging reviewer objected to marking a
packaging PEP Final because "tools have not rolled out support". PEP 1 itself sets one rule
for every PEP: Final once the reference implementation is complete and merged. So in this
snapshot, the remaining Accepted backlog is a packaging convention, not general neglect.

That breakdown was noticed after the job ran, so it is **exploratory**. A pre-registered
follow-up that measures it from the index file, `followups/topic/`, is filed and will be
reported here when it runs.

## Honest limits

- This is one snapshot. Statuses are kept by editors, and P1 shows that cleanup campaigns
  can move them a lot. A census taken before those campaigns might have found P1 HELD (not
  checked).
- P2 passed its threshold by one PEP.
- P5 is an association, not a cause. Editors can add or change the Python-Version header
  after acceptance, and packaging PEPs (most of them Final) usually have no Python-Version
  header at all. The follow-up repeats P5 without packaging PEPs.
- The index has no resolution dates (`resolution` is a link), so nothing here measures time
  to decision.

## Nearest prior work

Status pie charts and author graphs of PEPs (for example Noah Gorstein's "Exploring PEPs
with Python and Graphs"), qualitative mining of the PEP state machine, and the discussion
threads above. As far as a search on 2026-10-29 found, none of them grades fixed predictions
about outcomes across the whole corpus.

## Run it

    python -m unittest -v
    python job.py --data-dir ./data --out-dir ./out --allow-net

Standard library only, Python 3.10 or newer.

-- MV2, Munim, Inc.
