#!/usr/bin/env python3
"""PEP lifecycle census, follow-up 1: grade PREREG.md (F1-F3) against peps.json.

F1: Accepted-not-Final share by topic (packaging vs other).
F2: aged Draft/Deferred share at 4, 5 and 10 years.
F3: run 1's P5 (Python-Version vs Final share) without packaging PEPs.

Standard library only. Runs once in a sealed container:
    python topic_job.py --data-dir /data --out-dir /out
with /data/peps.json supplied by the compute lane (data_urls + data_key).
Code: Apache-2.0. By MV2 of Munim, Inc.; made with AI agents working in his name.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import urllib.request

PEPS_URL = "https://peps.python.org/api/peps.json"
AGE_YEARS = (4, 5, 10)


def parse_created(value):
    """Parse a PEP 'created' field (dd-mmm-yyyy); return date or None."""
    if not value:
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y"):
        try:
            return dt.datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def topics(p):
    return {t.strip().lower() for t in (p.get("topic") or "").split(",") if t.strip()}


def is_packaging(p):
    return "packaging" in topics(p)


def _share(num, den):
    return (num / den) if den else None


def _limbo(group):
    lim = sorted(p.get("number") for p in group if p.get("status") == "Accepted")
    return {"limbo": len(lim), "total": len(group),
            "share": _share(len(lim), len(group)), "limbo_peps": lim}


def _final_share(group):
    return _share(sum(p.get("status") == "Final" for p in group), len(group))


def compute(peps, snapshot):
    """peps: iterable of PEP dicts. snapshot: a date. Returns metrics dict."""
    peps = list(peps)
    st = [p for p in peps if p.get("type") == "Standards Track"]

    # F1: Accepted share among accepted (Accepted/Final) ST PEPs, by topic.
    acc = [p for p in st if p.get("status") in ("Accepted", "Final")]
    f1 = {"packaging": _limbo([p for p in acc if is_packaging(p)]),
          "other": _limbo([p for p in acc if not is_packaging(p)])}

    # F2: Draft/Deferred created at least N years before the snapshot.
    dated = [(p, parse_created(p.get("created"))) for p in peps]
    dated = [(p, c) for (p, c) in dated if c is not None]
    f2 = {"dated_peps": len(dated), "excluded_no_date": len(peps) - len(dated)}
    for years in AGE_YEARS:
        aged = [p for (p, c) in dated if p.get("status") in ("Draft", "Deferred")
                and (snapshot - c).days >= int(years * 365.25)]
        f2["%dy" % years] = {"n": len(aged), "share": _share(len(aged), len(dated))}
        if years == 5:
            f2["aged5_peps"] = {
                s: sorted(p.get("number") for p in aged if p.get("status") == s)
                for s in ("Draft", "Deferred")}

    # F3: P5 restricted to non-packaging ST PEPs (all-ST values kept for comparison).
    def p5(group):
        withv = [p for p in group if p.get("python_version")]
        nov = [p for p in group if not p.get("python_version")]
        w, n = _final_share(withv), _final_share(nov)
        return {"with_version_final_share": w, "without_version_final_share": n,
                "n_with_version": len(withv), "n_without_version": len(nov),
                "diff": (w - n) if (w is not None and n is not None) else None}
    f3 = {"non_packaging": p5([p for p in st if not is_packaging(p)]),
          "all_standards_track": p5(st)}

    topic_hist = {}
    for p in peps:
        for t in (topics(p) or {"(none)"}):
            topic_hist[t] = topic_hist.get(t, 0) + 1

    return {"n_peps": len(peps), "topic_hist": topic_hist,
            "F1": f1, "F2": f2, "F3": f3}


def grade(m):
    """Apply the PREREG.md decision rules; return {claim: verdict}."""
    g = {}
    pk, ot = m["F1"]["packaging"]["share"], m["F1"]["other"]["share"]
    if pk is None or ot is None:
        g["F1"] = "NULL"
    elif pk > 0.10 and ot < 0.02:
        g["F1"] = "HELD"
    elif pk <= ot:
        g["F1"] = "REVERSED"
    else:
        g["F1"] = "PARTIAL"

    s10 = m["F2"]["10y"]["share"]
    g["F2"] = "NULL" if s10 is None else ("HELD" if s10 > 0.03 else "REVERSED")

    d = m["F3"]["non_packaging"]["diff"]
    if d is None:
        g["F3"] = "NULL"
    elif d > 0.10:
        g["F3"] = "HELD"
    elif d < -0.02:
        g["F3"] = "REVERSED"
    else:
        g["F3"] = "NULL"
    return g


def find_peps_file(data_dir):
    """peps.json if present, else any other .json the data lane saved."""
    path = os.path.join(data_dir, "peps.json")
    if os.path.exists(path):
        return path
    others = sorted(glob.glob(os.path.join(data_dir, "*.json")))
    return others[0] if others else None


def load_peps(data_dir, allow_net):
    path = find_peps_file(data_dir)
    if path is None:
        if not allow_net:
            raise SystemExit("no peps.json in %s and --allow-net not set" % data_dir)
        req = urllib.request.Request(PEPS_URL, headers={"User-Agent": "mv2-munim-research/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return list(json.loads(resp.read().decode("utf-8")).values())
    with open(path, encoding="utf-8") as fh:
        return list(json.load(fh).values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--allow-net", action="store_true")
    ap.add_argument("--snapshot", default="", help="YYYY-MM-DD; default today")
    args = ap.parse_args()

    peps = load_peps(args.data_dir, args.allow_net)
    snapshot = (dt.date.fromisoformat(args.snapshot) if args.snapshot
                else dt.date.today())
    metrics = compute(peps, snapshot)
    summary = {"data_source": PEPS_URL, "snapshot_date": snapshot.isoformat(),
               "metrics": metrics, "verdicts": grade(metrics)}
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
