"""Self-contained tests for the PEP lifecycle verifier (no network).

A small hand-built fixture with known answers guards the metric and grading
logic in job.py.
"""
import datetime as dt
import json
import os
import tempfile
import unittest

import job

SNAP = dt.date(2026, 10, 29)


def pep(number, status, type_, created, python_version=None, authors=1):
    return {
        "number": number,
        "status": status,
        "type": type_,
        "created": created,
        "python_version": python_version,
        "author_names": ["A%d" % i for i in range(authors)],
    }


FIXTURE = [
    # Standards Track, accepted/final (P1 denominator = 4; limbo = 2 -> 50%).
    pep(100, "Accepted", "Standards Track", "01-Jan-2020", "3.9", authors=3),
    pep(101, "Accepted", "Standards Track", "01-Jan-2019", "3.8", authors=2),
    pep(102, "Final", "Standards Track", "01-Jan-2010", "3.2", authors=2),
    pep(103, "Final", "Standards Track", "01-Jan-2012", None, authors=3),
    # Aged Draft (created > 5y before SNAP) -> P2 numerator.
    pep(104, "Draft", "Standards Track", "01-Jan-2015", None, authors=1),
    pep(105, "Deferred", "Standards Track", "01-Jan-2016", None, authors=1),
    # Recent Draft -> not aged.
    pep(106, "Draft", "Standards Track", "01-Jan-2025", None, authors=1),
    # Negative Standards Track.
    pep(107, "Rejected", "Standards Track", "01-Jan-2011", None, authors=1),
    pep(108, "Withdrawn", "Standards Track", "01-Jan-2013", None, authors=4),
    # Process PEPs, none negative.
    pep(1, "Active", "Process", "13-Jun-2000", None, authors=2),
    pep(2, "Active", "Process", "07-Jul-2001", None, authors=1),
    # PEP with no created date -> excluded from P2.
    {"number": 999, "status": "Draft", "type": "Informational",
     "created": None, "python_version": None, "author_names": ["Z"]},
]


class TestCompute(unittest.TestCase):
    def setUp(self):
        self.m = job.compute(FIXTURE, SNAP)

    def test_counts(self):
        self.assertEqual(self.m["n_peps"], 12)
        self.assertEqual(self.m["excluded_no_date"], 1)

    def test_p1_accepted_limbo(self):
        # ST accepted/final = 100,101,102,103 (4); limbo = 100,101 (2).
        self.assertEqual(self.m["P1"]["accepted_total"], 4)
        self.assertEqual(self.m["P1"]["accepted_limbo"], 2)
        self.assertAlmostEqual(self.m["P1"]["share"], 0.5)

    def test_p2_aged_drafts(self):
        # Aged Draft/Deferred (>=5y before 2026): 104,105. dated peps = 11.
        self.assertEqual(self.m["P2"]["aged_drafts"], 2)
        self.assertEqual(self.m["P2"]["dated_peps"], 11)

    def test_p3_negative_shares(self):
        # ST = 100-108 (9); negative = 107,108 (2) -> 2/9. Process negative = 0.
        self.assertEqual(self.m["P3"]["n_standards_track"], 9)
        self.assertAlmostEqual(self.m["P3"]["standards_track_negative_share"], 2 / 9)
        self.assertEqual(self.m["P3"]["process_negative_share"], 0.0)

    def test_p4_authors(self):
        # Final authors: [2,3] -> median 2.5; Rej/Wd authors: [1,4] -> 2.5.
        self.assertAlmostEqual(self.m["P4"]["final_median_authors"], 2.5)
        self.assertAlmostEqual(self.m["P4"]["rejwd_median_authors"], 2.5)

    def test_p5_version_final_share(self):
        # ST with version: 100,101,102 -> Final among them = 102 -> 1/3.
        # ST without version: 103,104,105,106,107,108 -> Final = 103 -> 1/6.
        self.assertAlmostEqual(self.m["P5"]["with_version_final_share"], 1 / 3)
        self.assertAlmostEqual(self.m["P5"]["without_version_final_share"], 1 / 6)


class TestGrade(unittest.TestCase):
    def test_grades_from_fixture(self):
        g = job.grade(job.compute(FIXTURE, SNAP))
        self.assertEqual(g["P1"], "HELD")       # 0.5 > 0.10
        self.assertEqual(g["P2"], "HELD")       # 2/11 ~ 0.18 > 0.05
        self.assertEqual(g["P3"], "HELD")       # 0.22 - 0 > 0.02
        self.assertEqual(g["P4"], "NULL")       # 2.5 == 2.5
        self.assertEqual(g["P5"], "HELD")       # 0.333 - 0.167 > 0.02

    def test_parse_created(self):
        self.assertEqual(job.parse_created("13-Jun-2000"), dt.date(2000, 6, 13))
        self.assertIsNone(job.parse_created(None))
        self.assertIsNone(job.parse_created("not-a-date"))


class TestLoad(unittest.TestCase):
    def test_load_from_other_json_name(self):
        # The data lane may save the download under another name.
        index = {str(p["number"]): p for p in FIXTURE}
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "download.json"), "w", encoding="utf-8") as fh:
                json.dump(index, fh)
            peps = job.load_peps(d, allow_net=False)
        self.assertEqual(len(peps), 12)

    def test_missing_file_without_net_exits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                job.load_peps(d, allow_net=False)


if __name__ == "__main__":
    unittest.main()
