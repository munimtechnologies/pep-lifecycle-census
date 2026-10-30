#!/usr/bin/env python3
"""PEP lifecycle census: grade the pre-registration against peps.json.

Reads the authoritative Python Enhancement Proposal index and computes the
pre-registered statistics in prereg.md (P1-P5), writing a graded summary to
<out-dir>/summary.json.

Standard library only. Designed to run once in a sealed container:
    python job.py --data-dir /data --out-dir /out
with /data/peps.json supplied by the compute lane (data_urls + data_key).
If the file is absent and --allow-net is set, it is downloaded.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import statistics
import urllib.request

PEPS_URL = "https://peps.python.org/api/peps.json"

OPEN = {"Draft", "Deferred", "Provisional"}
NEGATIVE = {"Rejected", "Withdrawn", "Superseded"}

# PEPs named for the live spot-check recorded in the summary.
SPOTCHECK = ["8", "484", "505", "563", "649", "3150"]


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


def _share(num, den):
    return (num / den) if den else None


def compute(peps, snapshot):
    """peps: iterable of PEP dicts. snapshot: a date. Returns metrics dict."""
    peps = list(peps)

    def is_type(p, t):
        return (p.get("type") or "") == t

    def status(p):
        return p.get("status") or ""

    def nauthors(p):
        names = p.get("author_names")
        return len(names) if isinstance(names, list) else (1 if p.get("authors") else 0)

    # P1: Accepted-not-Final among accepted Standards Track PEPs.
    st_accepted = [p for p in peps if is_type(p, "Standards Track")
                   and status(p) in ("Accepted", "Final")]
    st_accepted_limbo = [p for p in st_accepted if status(p) == "Accepted"]
    p1_share = _share(len(st_accepted_limbo), len(st_accepted))

    # P2: aged drafts (Draft/Deferred, created >= 5y ago) over all dated PEPs.
    dated = [(p, parse_created(p.get("created"))) for p in peps]
    dated = [(p, c) for (p, c) in dated if c is not None]
    excluded_no_date = len(peps) - len(dated)
    aged_drafts = [p for (p, c) in dated
                   if status(p) in ("Draft", "Deferred")
                   and (snapshot - c).days >= int(5 * 365.25)]
    p2_share = _share(len(aged_drafts), len(dated))

    # P3: NEGATIVE share, Standards Track vs Process.
    st = [p for p in peps if is_type(p, "Standards Track")]
    proc = [p for p in peps if is_type(p, "Process")]
    p3_st = _share(sum(status(p) in NEGATIVE for p in st), len(st))
    p3_proc = _share(sum(status(p) in NEGATIVE for p in proc), len(proc))

    # P4: author count, Final vs Rejected/Withdrawn.
    final_auth = [nauthors(p) for p in peps if status(p) == "Final"]
    rejwd_auth = [nauthors(p) for p in peps if status(p) in ("Rejected", "Withdrawn")]
    p4_final = statistics.median(final_auth) if final_auth else None
    p4_rejwd = statistics.median(rejwd_auth) if rejwd_auth else None

    # P5: Final share among Standards Track, with vs without python_version.
    st_withv = [p for p in st if p.get("python_version")]
    st_nov = [p for p in st if not p.get("python_version")]
    p5_withv = _share(sum(status(p) == "Final" for p in st_withv), len(st_withv))
    p5_nov = _share(sum(status(p) == "Final" for p in st_nov), len(st_nov))

    status_hist = {}
    type_hist = {}
    for p in peps:
        status_hist[status(p)] = status_hist.get(status(p), 0) + 1
        type_hist[(p.get("type") or "")] = type_hist.get((p.get("type") or ""), 0) + 1

    return {
        "n_peps": len(peps),
        "excluded_no_date": excluded_no_date,
        "status_hist": status_hist,
        "type_hist": type_hist,
        "P1": {"accepted_limbo": len(st_accepted_limbo),
               "accepted_total": len(st_accepted), "share": p1_share},
        "P2": {"aged_drafts": len(aged_drafts), "dated_peps": len(dated),
               "share": p2_share},
        "P3": {"standards_track_negative_share": p3_st,
               "process_negative_share": p3_proc,
               "n_standards_track": len(st), "n_process": len(proc)},
        "P4": {"final_median_authors": p4_final,
               "rejwd_median_authors": p4_rejwd,
               "n_final": len(final_auth), "n_rejwd": len(rejwd_auth)},
        "P5": {"with_version_final_share": p5_withv,
               "without_version_final_share": p5_nov,
               "n_with_version": len(st_withv), "n_without_version": len(st_nov)},
    }


def grade(m):
    """Apply the prereg decision rules; return {claim: verdict}."""
    g = {}
    s1 = m["P1"]["share"]
    g["P1"] = ("HELD" if s1 is not None and s1 > 0.10 else "REVERSED") if s1 is not None else "NULL"

    s2 = m["P2"]["share"]
    g["P2"] = ("HELD" if s2 is not None and s2 > 0.05 else "REVERSED") if s2 is not None else "NULL"

    a, b = m["P3"]["standards_track_negative_share"], m["P3"]["process_negative_share"]
    if a is None or b is None:
        g["P3"] = "NULL"
    elif a - b > 0.02:
        g["P3"] = "HELD"
    elif b - a > 0.02:
        g["P3"] = "REVERSED"
    else:
        g["P3"] = "NULL"

    f, r = m["P4"]["final_median_authors"], m["P4"]["rejwd_median_authors"]
    if f is None or r is None:
        g["P4"] = "NULL"
    elif f > r:
        g["P4"] = "HELD"
    elif f < r:
        g["P4"] = "REVERSED"
    else:
        g["P4"] = "NULL"

    w, n = m["P5"]["with_version_final_share"], m["P5"]["without_version_final_share"]
    if w is None or n is None:
        g["P5"] = "NULL"
    elif w - n > 0.02:
        g["P5"] = "HELD"
    elif n - w > 0.02:
        g["P5"] = "REVERSED"
    else:
        g["P5"] = "NULL"
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
            raw = resp.read()
        path = os.path.join(data_dir, "peps.json")
        try:
            os.makedirs(data_dir, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(raw)
        except OSError:
            return list(json.loads(raw.decode("utf-8")).values())
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    # Index is keyed by PEP number (string); values are the PEP objects.
    return list(data.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="/data")
    ap.add_argument("--out-dir", default="/out")
    ap.add_argument("--allow-net", action="store_true")
    args = ap.parse_args()

    peps = load_peps(args.data_dir, args.allow_net)
    by_num = {str(p.get("number")): p for p in peps}
    snapshot = dt.date.today()
    metrics = compute(peps, snapshot)
    verdicts = grade(metrics)
    spot = {n: (by_num[n]["status"] if n in by_num else None) for n in SPOTCHECK}

    summary = {
        "data_source": PEPS_URL,
        "snapshot_date": snapshot.isoformat(),
        "metrics": metrics,
        "verdicts": verdicts,
        "spotcheck_status": spot,
    }
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    print(json.dumps({"verdicts": verdicts,
                      "n_peps": metrics["n_peps"],
                      "metrics": metrics,
                      "spotcheck_status": spot}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
