#!/usr/bin/env python3
"""Build a kill matrix from a mutation-testing report and find tests that don't earn their place.

A test earns its place when it kills a mutant that no other kept test kills.

Reports, detected automatically:
  * mutation-testing-report-schema JSON, as written by StrykerJS and Stryker.NET:
    files[*].mutants[*] with status, killedBy and coveredBy; testFiles[*].tests[*] for names.
  * PIT mutations.xml. Run PIT with fullMutationMatrix=true, or the matrix is incomplete.
  * CSV with a header row: mutant,status,killed_by[,covered_by][,location][,mutator]
    where killed_by and covered_by hold test names separated by "|".

Usage:
  python3 kill_matrix.py REPORT [--contract-dir contract] [--full-matrix]
                         [--min-score N] [--max-list N] [--json]

Deletion advice is withheld when the report looks like the tool stopped at the first
killing test, because then a test that happened to run second looks useless. Pass
--full-matrix when you know every killing test was recorded.

Exit status is 1 when --min-score is given and the mutation score is below it, 2 when
the report can't be read, and 0 otherwise.
"""

import argparse
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

OBLIGATION_HEADING = re.compile(r"^###\s+([A-Z][A-Z0-9]{1,9})-(\d{3,})[:.,]?(?:\s+\[([^\]]*)\])?")
STATUSES = {
    "killed": "killed", "caught": "killed",
    "timeout": "timeout", "timedout": "timeout", "memoryerror": "timeout",
    "runerror": "timeout", "suspicious": "timeout",
    "survived": "survived", "lived": "survived", "missed": "survived",
    "nocoverage": "no_coverage", "notcovered": "no_coverage", "notests": "no_coverage",
    "compileerror": "invalid", "runtimeerror": "invalid", "nonviable": "invalid",
    "unviable": "invalid",
}


def normalize_status(raw):
    return STATUSES.get(re.sub(r"[^a-z]", "", (raw or "").lower()), "ignored")


def split_tests(value):
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def pretty_pit_name(name):
    test_class = re.search(r"\[class:([^\]]+)\]", name)
    method = re.search(r"\[(?:method|test-template|test-factory):([^\]]+)\]", name)
    if test_class and method:
        return "{}.{}".format(test_class.group(1), method.group(1))
    return name


def load_stryker(data):
    tests = {}
    for test_file, entry in (data.get("testFiles") or {}).items():
        for test in entry.get("tests") or []:
            tests[str(test["id"])] = {"name": test.get("name") or str(test["id"]),
                                      "file": test_file}
    mutants = []
    for source, entry in (data.get("files") or {}).items():
        for mutant in entry.get("mutants") or []:
            start = (mutant.get("location") or {}).get("start") or {}
            covered = mutant.get("coveredBy")
            mutants.append({
                "id": "{}#{}".format(source, mutant.get("id")),
                "location": "{}:{}".format(source, start.get("line", "?")),
                "mutator": mutant.get("mutatorName") or "",
                "description": mutant.get("replacement") or mutant.get("description") or "",
                "status": normalize_status(mutant.get("status")),
                "killed_by": {str(t) for t in mutant.get("killedBy") or []},
                "covered_by": None if covered is None else {str(t) for t in covered},
            })
    return mutants, tests, None


def load_pit(root):
    mutants, tests, complete = [], {}, False
    for index, node in enumerate(root.iter("mutation")):
        def text(tag):
            return (node.findtext(tag) or "").strip()
        if node.find("killingTests") is not None:
            complete = True
            killers = split_tests(node.findtext("killingTests"))
        else:
            killers = split_tests(node.findtext("killingTest"))
        succeeding = node.find("succeedingTests")
        covered = None
        if succeeding is not None:
            covered = set(killers) | set(split_tests(succeeding.text))
        mutator = text("mutator").rsplit(".", 1)[-1]
        line = text("lineNumber")
        mutants.append({
            "id": "{}:{}:{}:{}".format(text("mutatedClass"), line, mutator, index),
            "location": "{}:{}".format(text("sourceFile") or text("mutatedClass"), line),
            "mutator": mutator,
            "description": text("description"),
            "status": normalize_status(node.get("status")),
            "killed_by": set(killers),
            "covered_by": covered,
        })
        for test in set(killers) | (covered or set()):
            tests.setdefault(test, {"name": pretty_pit_name(test), "file": None})
    return mutants, tests, complete


def load_csv(handle):
    reader = csv.DictReader(handle)
    fields = {(f or "").strip().lower() for f in reader.fieldnames or []}
    if not {"mutant", "status"} <= fields:
        raise ValueError("CSV needs a header row with at least: mutant,status,killed_by")
    has_coverage = "covered_by" in fields
    mutants, tests = [], {}
    for row in reader:
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        killers = split_tests(row.get("killed_by"))
        covered = set(split_tests(row.get("covered_by"))) | set(killers) if has_coverage else None
        mutants.append({
            "id": row["mutant"],
            "location": row.get("location") or row["mutant"],
            "mutator": row.get("mutator", ""),
            "description": row.get("description", ""),
            "status": normalize_status(row["status"]),
            "killed_by": set(killers),
            "covered_by": covered,
        })
        for test in set(killers) | (covered or set()):
            tests.setdefault(test, {"name": test, "file": None})
    return mutants, tests, None


def load_report(path):
    with open(path, "rb") as handle:
        head = handle.read(4096).lstrip()
    if head.startswith(b"{"):
        with open(path, encoding="utf-8") as handle:
            return ("mutation-testing-report-schema JSON",) + load_stryker(json.load(handle))
    if head.startswith(b"<"):
        return ("PIT XML",) + load_pit(ET.parse(path).getroot())
    with open(path, encoding="utf-8", newline="") as handle:
        return ("CSV",) + load_csv(handle)


def load_obligations(contract_dir):
    keys = set()
    if not contract_dir or not os.path.isdir(contract_dir):
        return keys
    for directory, _, files in os.walk(contract_dir):
        for name in files:
            if not name.lower().endswith(".md"):
                continue
            in_fence = False
            with open(os.path.join(directory, name), encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if line.lstrip().startswith(("```", "~~~")):
                        in_fence = not in_fence
                        continue
                    match = None if in_fence else OBLIGATION_HEADING.match(line)
                    if match and (match.group(3) or "").strip().lower() != "retired":
                        keys.add((match.group(1), int(match.group(2))))
    return keys


def obligation_finder(keys):
    prefixes = sorted({prefix for prefix, _ in keys}, key=len, reverse=True)
    if not prefixes:
        return lambda text: set()
    pattern = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(p) for p in prefixes)
                         + r")[-_](\d+)(?![0-9])", re.I)

    def find(text):
        found = {(m.group(1).upper(), int(m.group(2))) for m in pattern.finditer(text or "")}
        return found & keys
    return find


def analyse(mutants, tests, complete, obligation_keys, trust_matrix):
    counts = defaultdict(int)
    for mutant in mutants:
        counts[mutant["status"]] += 1
    detected = counts["killed"] + counts["timeout"]
    valid = detected + counts["survived"] + counts["no_coverage"]
    score = round(100.0 * detected / valid, 2) if valid else None

    kills, covers = defaultdict(set), defaultdict(set)
    coverage_known = any(m["covered_by"] is not None for m in mutants)
    unattributed = 0
    for mutant in mutants:
        if mutant["status"] == "killed":
            if mutant["killed_by"]:
                for test in mutant["killed_by"]:
                    kills[test].add(mutant["id"])
            else:
                unattributed += 1
        for test in mutant["covered_by"] or ():
            covers[test].add(mutant["id"])
    for test in set(kills) | set(covers):
        tests.setdefault(test, {"name": test, "file": None})

    warnings = []
    killed_with_killers = [m for m in mutants if m["status"] == "killed" and m["killed_by"]]
    if complete is None and len(killed_with_killers) >= 10 and len(kills) > 1:
        if not any(len(m["killed_by"]) > 1 for m in killed_with_killers):
            complete = False
    if complete is False and not trust_matrix:
        warnings.append(
            "Every killed mutant lists only its first killing test, so a test that ran second "
            "looks useless. Re-run with the full matrix (StrykerJS disableBail, Stryker.NET "
            "disable-bail, PIT fullMutationMatrix=true), or pass --full-matrix if it already "
            "was. Deletion advice withheld.")
    if unattributed:
        warnings.append(
            "{} killed mutants don't say which test killed them; enable per-test coverage "
            "(Stryker coverageAnalysis: perTest).".format(unattributed))
    if not kills and counts["killed"]:
        warnings.append("The report has no killing-test data at all. Deletion advice withheld.")
    advice = bool(kills) and (complete is not False or trust_matrix)

    find = obligation_finder(obligation_keys)
    carries = {t: find(tests[t]["name"]) | find(t) for t in tests}

    ordered = sorted(kills, key=lambda t: tests[t]["name"])
    uncovered = set().union(*kills.values()) if kills else set()
    retained = []
    while uncovered and ordered:
        best = max(ordered, key=lambda t: (len(kills[t] & uncovered), bool(carries[t]),
                                           len(kills[t])))
        gain = kills[best] & uncovered
        if not gain:
            break
        retained.append(best)
        ordered.remove(best)
        uncovered -= gain

    holders = defaultdict(int)
    for test in retained:
        for mutant in kills[test]:
            holders[mutant] += 1
    for test in sorted(retained, key=lambda t: (bool(carries[t]), len(kills[t]),
                                                 tests[t]["name"])):
        if all(holders[m] > 1 for m in kills[test]):
            retained.remove(test)
            for mutant in kills[test]:
                holders[mutant] -= 1
    kept = set(retained)

    protected = set()
    for key in sorted(obligation_keys):
        carriers = [t for t in tests if key in carries[t]]
        if carriers and not any(t in kept for t in carriers):
            protected.add(max(sorted(carriers, key=lambda t: tests[t]["name"]),
                              key=lambda t: len(kills.get(t, ()))))

    def describe(test, **extra):
        item = {"test": tests[test]["name"], "file": tests[test]["file"],
                "kills": len(kills.get(test, ())),
                "obligations": ["{}-{:03d}".format(*k) for k in sorted(carries[test])]}
        item.update(extra)
        return item

    redundant = [describe(t) for t in sorted(kills, key=lambda t: tests[t]["name"])
                 if t not in kept and t not in protected]
    zero_kill, idle = [], []
    for test in sorted(tests, key=lambda t: tests[t]["name"]):
        if kills.get(test) or test in protected:
            continue
        (zero_kill if covers.get(test) else idle).append(describe(test))
    if not advice:
        redundant, zero_kill = [], []

    survivors = [{"location": m["location"], "mutator": m["mutator"], "status": m["status"],
                  "description": m["description"]}
                 for m in mutants if m["status"] in ("survived", "no_coverage")]
    survivors.sort(key=lambda s: s["location"])

    return {
        "score": score,
        "counts": {"mutants": len(mutants), "killed": counts["killed"],
                   "timeout": counts["timeout"], "survived": counts["survived"],
                   "no_coverage": counts["no_coverage"], "invalid": counts["invalid"],
                   "ignored": counts["ignored"], "tests": len(tests), "retained": len(kept),
                   "redundant": len(redundant), "zero_kill": len(zero_kill),
                   "protected": len(protected), "idle": len(idle)},
        "advice": advice,
        "matrix_complete": complete,
        "coverage_known": coverage_known,
        "survivors": survivors,
        "retained": [describe(t, unique=sum(1 for m in kills[t] if holders[m] == 1))
                     for t in sorted(kept, key=lambda t: tests[t]["name"])],
        "redundant": redundant,
        "zero_kill": zero_kill,
        "protected": [describe(t) for t in sorted(protected, key=lambda t: tests[t]["name"])],
        "idle": idle,
        "warnings": warnings,
    }


def label(item):
    text = item["test"]
    if item.get("file"):
        text += " ({})".format(item["file"])
    if item.get("obligations"):
        text += " [{}]".format(", ".join(item["obligations"]))
    return text


def print_list(title, items, limit, render):
    if not items:
        return
    print()
    print(title)
    for item in items[:limit]:
        print("  " + render(item))
    if len(items) > limit:
        print("  ... and {} more (use --json for all)".format(len(items) - limit))


def print_text(result, source, limit):
    c = result["counts"]
    if result["score"] is None:
        print("Mutation score: n/a (no valid mutants)  [{}]".format(source))
    else:
        print("Mutation score: {:.1f}% ({} of {} detected; {} survived, {} without coverage, "
              "{} invalid, {} ignored)  [{}]".format(
                  result["score"], c["killed"] + c["timeout"],
                  c["killed"] + c["timeout"] + c["survived"] + c["no_coverage"],
                  c["survived"], c["no_coverage"], c["invalid"], c["ignored"], source))
    if result["advice"]:
        print("Tests: {tests} known, {retained} retained, {redundant} redundant, {zero_kill} "
              "zero-kill, {protected} protected, {idle} not exercised".format(**c))
    else:
        print("Tests: {tests} known, {protected} protected; deletion advice withheld "
              "(see warnings)".format(**c))
    print_list("Survivors ({}): each is a missing obligation, unneeded code, or an equivalent "
               "mutant.".format(len(result["survivors"])), result["survivors"], limit,
               lambda s: "{}  {}  {}  {}".format(s["location"], s["mutator"], s["status"],
                                                 s["description"]).rstrip())
    print_list("Redundant tests ({}): every mutant they kill is killed by a retained test. "
               "Delete them.".format(len(result["redundant"])), result["redundant"], limit,
               lambda i: "{}  kills {}".format(label(i), i["kills"]))
    print_list("Zero-kill tests ({}): they run mutated code and kill nothing. Delete them, or "
               "make them assert something.".format(len(result["zero_kill"])),
               result["zero_kill"], limit, label)
    print_list("Protected tests ({}): the only tests citing an obligation, with no unique kill. "
               "Keep and strengthen them.".format(len(result["protected"])),
               result["protected"], limit, lambda i: "{}  kills {}".format(label(i), i["kills"]))
    if result["warnings"]:
        print()
        print("Warnings:")
        for warning in result["warnings"]:
            print("  " + warning)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a kill matrix and find tests that don't earn their place.")
    parser.add_argument("report", help="Stryker JSON, PIT mutations.xml, or CSV report")
    parser.add_argument("--contract-dir", default="contract",
                        help="IMP Contract folder, to protect the last test of each obligation")
    parser.add_argument("--full-matrix", action="store_true",
                        help="trust that the report records every killing test")
    parser.add_argument("--min-score", type=float, metavar="N",
                        help="exit 1 when the mutation score is below N percent")
    parser.add_argument("--max-list", type=int, default=50, metavar="N",
                        help="longest list to print in text mode (default 50)")
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    args = parser.parse_args(argv)

    try:
        source, mutants, tests, complete = load_report(args.report)
    except (OSError, ValueError, ET.ParseError, KeyError) as error:
        print("Can't read {}: {}".format(args.report, error), file=sys.stderr)
        return 2

    obligations = load_obligations(args.contract_dir)
    result = analyse(mutants, tests, complete, obligations, args.full_matrix)
    if not obligations and args.contract_dir:
        result["warnings"].append(
            "No obligations found in '{}', so no test is protected as the last executable form "
            "of an obligation.".format(args.contract_dir))

    below = (args.min_score is not None and result["score"] is not None
             and result["score"] < args.min_score)
    if args.json:
        result["source"] = source
        result["min_score_failed"] = below
        print(json.dumps(result, indent=2))
    else:
        print_text(result, source, args.max_list)
        if below:
            print()
            print("FAIL: mutation score {:.1f}% is below {:.1f}%".format(
                result["score"], args.min_score))
    return 1 if below else 0


if __name__ == "__main__":
    sys.exit(main())
