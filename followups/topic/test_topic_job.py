"""Self-contained tests for follow-up 1 (no network).

A small hand-built fixture with known answers guards the metric and grading
logic in topic_job.py. Code: Apache-2.0.
"""
import datetime as dt
import json
import os
import tempfile
import unittest

import topic_job

SNAP = dt.date(2026, 10, 30)


def pep(number, status, type_, created, topic="", python_version=None):
    return {"number": number, "status": status, "type": type_, "created": created,
            "topic": topic, "python_version": python_version, "author_names": ["A"]}


FIXTURE = [
    pep(1001, "Accepted", "Standards Track", "01-Jan-2024", "packaging"),
    pep(1002, "Final", "Standards Track", "01-Jan-2018", "packaging"),
    pep(1003, "Final", "Standards Track", "01-Jan-2019", "packaging"),
    pep(1004, "Final", "Standards Track", "01-Jan-2010", "", "3.2"),
    pep(1005, "Final", "Standards Track", "01-Jan-2015", "typing", "3.5"),
    pep(1006, "Accepted", "Standards Track", "01-Jan-2025", "", "3.15"),
    # 5416 days old: aged at 4, 5 and 10 years.
    pep(1007, "Draft", "Standards Track", "01-Jan-2012", ""),
    # 2128 days old: aged at 4 and 5 years, not 10.
    pep(1008, "Deferred", "Standards Track", "01-Jan-2021", "packaging"),
    # 1398 days old: not aged at any threshold.
    pep(1009, "Draft", "Standards Track", "01-Jan-2023", ""),
    pep(1010, "Rejected", "Standards Track", "01-Jan-2011", "", "3.3"),
    pep(1011, "Active", "Process", "01-Jan-2000", "governance"),
    # No created date: excluded from F2; two topics.
    {"number": 1012, "status": "Draft", "type": "Informational", "created": None,
     "topic": "Release, packaging", "python_version": None, "author_names": ["B"]},
]


class TestCompute(unittest.TestCase):
    def setUp(self):
        self.m = topic_job.compute(FIXTURE, SNAP)

    def test_topics(self):
        self.assertEqual(topic_job.topics(FIXTURE[11]), {"release", "packaging"})
        self.assertEqual(self.m["topic_hist"],
                         {"packaging": 5, "typing": 1, "governance": 1,
                          "release": 1, "(none)": 5})

    def test_f1_limbo_by_topic(self):
        f1 = self.m["F1"]
        self.assertEqual((f1["packaging"]["limbo"], f1["packaging"]["total"]), (1, 3))
        self.assertEqual(f1["packaging"]["limbo_peps"], [1001])
        self.assertEqual((f1["other"]["limbo"], f1["other"]["total"]), (1, 3))
        self.assertEqual(f1["other"]["limbo_peps"], [1006])

    def test_f2_thresholds(self):
        f2 = self.m["F2"]
        self.assertEqual(f2["dated_peps"], 11)
        self.assertEqual(f2["excluded_no_date"], 1)
        self.assertEqual(f2["4y"]["n"], 2)
        self.assertEqual(f2["5y"]["n"], 2)
        self.assertEqual(f2["10y"]["n"], 1)
        self.assertAlmostEqual(f2["10y"]["share"], 1 / 11)
        self.assertEqual(f2["aged5_peps"], {"Draft": [1007], "Deferred": [1008]})

    def test_f3_without_packaging(self):
        npk = self.m["F3"]["non_packaging"]
        # With version: 1004 F, 1005 F, 1006 A, 1010 R -> 2/4. Without: 1007, 1009 -> 0/2.
        self.assertEqual((npk["n_with_version"], npk["n_without_version"]), (4, 2))
        self.assertAlmostEqual(npk["with_version_final_share"], 0.5)
        self.assertEqual(npk["without_version_final_share"], 0.0)
        self.assertAlmostEqual(npk["diff"], 0.5)
        allst = self.m["F3"]["all_standards_track"]
        # Without version (all ST): 1001-1003, 1007-1009 -> Final 1002, 1003 -> 2/6.
        self.assertEqual(allst["n_without_version"], 6)
        self.assertAlmostEqual(allst["without_version_final_share"], 1 / 3)


def metrics(pk, ot, s10, diff):
    return {"F1": {"packaging": {"share": pk}, "other": {"share": ot}},
            "F2": {"10y": {"share": s10}},
            "F3": {"non_packaging": {"diff": diff}}}


class TestGrade(unittest.TestCase):
    def test_fixture_grades(self):
        g = topic_job.grade(topic_job.compute(FIXTURE, SNAP))
        self.assertEqual(g, {"F1": "REVERSED", "F2": "HELD", "F3": "HELD"})

    def test_held(self):
        g = topic_job.grade(metrics(0.17, 0.0, 0.04, 0.3))
        self.assertEqual(g, {"F1": "HELD", "F2": "HELD", "F3": "HELD"})

    def test_partial_reversed_null(self):
        g = topic_job.grade(metrics(0.17, 0.05, 0.03, 0.05))
        self.assertEqual(g, {"F1": "PARTIAL", "F2": "REVERSED", "F3": "NULL"})
        g = topic_job.grade(metrics(0.01, 0.0, 0.02, -0.03))
        self.assertEqual(g, {"F1": "PARTIAL", "F2": "REVERSED", "F3": "REVERSED"})

    def test_missing(self):
        g = topic_job.grade(metrics(None, 0.0, None, None))
        self.assertEqual(g, {"F1": "NULL", "F2": "NULL", "F3": "NULL"})


class TestLoad(unittest.TestCase):
    def test_load_from_other_json_name(self):
        index = {str(p["number"]): p for p in FIXTURE}
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "download.json"), "w", encoding="utf-8") as fh:
                json.dump(index, fh)
            self.assertEqual(len(topic_job.load_peps(d, allow_net=False)), 12)

    def test_missing_file_without_net_exits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                topic_job.load_peps(d, allow_net=False)


if __name__ == "__main__":
    unittest.main()
