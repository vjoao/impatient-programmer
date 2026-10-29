#!/usr/bin/env python3
"""Check an IMP Contract: obligation format, unique IDs, and test coverage.

Obligations are level-3 headings inside a level-2 section whose title contains
"obligations" (for example "## Obligations" or "## Cross-cutting obligations"):

    ### QUO-004 [latency] Quotes return inside the checkout timeout
    The quote service shall respond within 120 ms at p99 at 50 requests per second.

An obligation is tested when a test file cites its ID (QUO-004, QUO_004 or quo_004).
A "Verified by: manual" line exempts it from needing a test; kind [retired] retires it.
IDs under other sections, such as "## Unconfirmed", are tracked but not enforced.

Usage:
    python3 check_contract.py [--contract-dir contract] [--tests DIR ...]
                              [--all-files] [--strict] [--json]

Exit status is 1 on format errors or on tests citing unknown or retired IDs, and,
with --strict, when an active obligation has no test. Otherwise 0.
"""

import argparse
import json
import os
import re
import sys

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
OBLIGATION = re.compile(r"^(\S+)(?:\s+\[([^\]]*)\])?\s*(.*)$")
VALID_ID = re.compile(r"^([A-Z][A-Z0-9]{1,9})-(\d{3,})$")
ID_LIKE = re.compile(r"^[A-Za-z][A-Za-z0-9]{1,9}[-_]\d+$")
FENCE = re.compile(r"^\s*(```|~~~)")
MANUAL = re.compile(r"^\s*(?:[-*]\s*)?verified by:\s*manual\b", re.I)
SHALL = re.compile(r"\bshall\b", re.I)

DEFAULT_TEST_DIRS = ["test", "tests", "spec", "specs", "__tests__", "Tests",
                     "src", "app", "lib", "packages"]
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "target", "out",
             ".venv", "venv", "Pods", ".next", "coverage", "reports", "DerivedData",
             ".gradle", "__pycache__", ".tox", ".idea"}
TEST_DIR_NAMES = {"test", "tests", "spec", "specs", "__tests__", "e2e", "contract-tests"}
CODE_EXTENSIONS = {".py", ".rb", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go",
                   ".rs", ".java", ".kt", ".kts", ".swift", ".cs", ".fs", ".scala",
                   ".php", ".ex", ".exs", ".erl", ".clj", ".cljs", ".dart", ".lua",
                   ".m", ".mm", ".c", ".cc", ".cpp", ".h", ".hpp", ".feature",
                   ".sh", ".bats", ".robot", ".yml", ".yaml"}
SEVERITY_ORDER = {"error": 0, "untested": 1, "warning": 2}


def problem(severity, code, path, line, obligation_id, message):
    return {"severity": severity, "code": code, "file": path, "line": line,
            "id": obligation_id, "message": message}


def markdown_files(root):
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS)
        for name in sorted(files):
            if name.lower().endswith(".md"):
                yield os.path.join(directory, name)


def parse_heading(text, section, path, line, entries, problems):
    in_obligations = "obligation" in section.lower()
    match = OBLIGATION.match(text)
    token = match.group(1).rstrip(":.,")
    kind = (match.group(2) or "").strip().lower()
    title = match.group(3).strip().lstrip("—–-: ").strip()
    if not VALID_ID.match(token):
        if in_obligations and ID_LIKE.match(token):
            problems.append(problem(
                "error", "malformed-id", path, line, token,
                "obligation IDs look like QUO-004: a 2-10 character uppercase prefix, "
                "a hyphen, and at least 3 digits"))
        elif in_obligations:
            problems.append(problem(
                "warning", "no-id", path, line, None,
                "heading in an obligations section has no obligation ID: " + text))
        return None
    if not in_obligations:
        status = "unconfirmed"
    elif kind == "retired":
        status = "retired"
    else:
        status = "active"
    entry = {"id": token, "kind": kind or None, "title": title, "file": path,
             "line": line, "section": section, "status": status, "body": [], "tests": []}
    entries.append(entry)
    return entry


def parse_contract(contract_dir):
    entries, problems = [], []
    for path in markdown_files(contract_dir):
        with open(path, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        start = 0
        if lines and lines[0].strip() == "---":
            for index in range(1, len(lines)):
                if lines[index].strip() == "---":
                    start = index + 1
                    break
        section, current, in_fence = "", None, False
        for index in range(start, len(lines)):
            line = lines[index]
            if FENCE.match(line):
                in_fence = not in_fence
            heading = None if in_fence else HEADING.match(line)
            if heading:
                level = len(heading.group(1))
                if level <= 3:
                    current = None
                if level == 2:
                    section = heading.group(2)
                elif level == 3:
                    current = parse_heading(heading.group(2), section, path, index + 1,
                                            entries, problems)
                if level <= 3:
                    continue
            if current is not None:
                current["body"].append(line)
    return entries, problems


def key_of(obligation_id):
    prefix, number = re.split(r"[-_]", obligation_id, maxsplit=1)
    return prefix.upper(), int(number)


def is_test_path(path):
    parts = path.replace(os.sep, "/").split("/")
    for directory in parts[:-1]:
        if directory.lower() in TEST_DIR_NAMES or directory.endswith(("Tests", "Test")):
            return True
    name = parts[-1]
    lowered = name.lower()
    stem = name.split(".")[0]
    return (lowered.startswith("test_")
            or re.search(r"[._-](test|spec)s?\.", lowered) is not None
            or re.search(r"(Test|Tests|Spec|IT)$", stem) is not None)


def file_identity(path):
    status = os.stat(path)
    return status.st_dev, status.st_ino


def unique_folders(folders):
    seen, unique = set(), []
    for folder in folders:
        identity = file_identity(folder)
        if identity not in seen:
            seen.add(identity)
            unique.append(folder)
    return unique


def source_files(roots, all_files):
    seen = set()
    for root in roots:
        for directory, subdirs, files in os.walk(root):
            subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS)
            for name in sorted(files):
                path = os.path.join(directory, name)
                if os.path.splitext(name)[1].lower() not in CODE_EXTENSIONS:
                    continue
                if not all_files and not is_test_path(os.path.relpath(path)):
                    continue
                identity = file_identity(path)
                if identity not in seen:
                    seen.add(identity)
                    yield path


def scan_tests(roots, prefixes, all_files):
    references = {}
    if not prefixes:
        return references
    alternatives = "|".join(re.escape(p) for p in sorted(prefixes, key=len, reverse=True))
    pattern = re.compile(r"(?<![A-Za-z0-9])(" + alternatives + r")[-_](\d+)(?![0-9])", re.I)
    for path in source_files(roots, all_files):
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                for number, line in enumerate(handle, start=1):
                    for match in pattern.finditer(line):
                        key = (match.group(1).upper(), int(match.group(2)))
                        references.setdefault(key, []).append((path, number))
        except OSError:
            continue
    return references


def check(contract_dir, test_roots, all_files):
    entries, problems = parse_contract(contract_dir)

    first_seen = {}
    for entry in entries:
        key = key_of(entry["id"])
        if key in first_seen:
            original = first_seen[key]
            problems.append(problem(
                "error", "duplicate-id", entry["file"], entry["line"], entry["id"],
                "duplicate ID (first at {}:{})".format(original["file"], original["line"])))
        else:
            first_seen[key] = entry

    for entry in entries:
        if entry["status"] != "active":
            continue
        body = entry.pop("body")
        entry["manual"] = any(MANUAL.match(line) for line in body)
        if not any(SHALL.search(line) for line in body):
            problems.append(problem(
                "warning", "no-statement", entry["file"], entry["line"], entry["id"],
                "no EARS statement: write one sentence with 'shall'"))
    for entry in entries:
        entry.pop("body", None)
        entry.setdefault("manual", False)

    prefixes = {key_of(entry["id"])[0] for entry in entries}
    references = scan_tests(test_roots, prefixes, all_files)

    by_key = {}
    for entry in entries:
        by_key.setdefault(key_of(entry["id"]), []).append(entry)
    for key, locations in sorted(references.items()):
        group = by_key.get(key)
        cited = "{}-{:03d}".format(*key)
        for path, line in locations:
            if group is None:
                problems.append(problem(
                    "error", "unknown-id", path, line, cited,
                    "test cites an obligation that is not in the Contract"))
            elif group[0]["status"] == "retired":
                problems.append(problem(
                    "error", "retired-id", path, line, group[0]["id"],
                    "test cites a retired obligation; delete or retarget the test"))
        for entry in group or []:
            entry["tests"] = ["{}:{}".format(path, line) for path, line in locations]

    for entry in entries:
        if entry["status"] == "active" and not entry["manual"] and not entry["tests"]:
            problems.append(problem(
                "untested", "untested", entry["file"], entry["line"], entry["id"],
                "no test cites {0}; add one, or 'Verified by: manual — <reason>'".format(
                    entry["id"])))

    for entry in entries:
        if entry["status"] == "active":
            entry["verification"] = "manual" if entry["manual"] else (
                "tested" if entry["tests"] else "untested")
        else:
            entry["verification"] = entry["status"]
        del entry["manual"]

    problems.sort(key=lambda p: (SEVERITY_ORDER[p["severity"]], p["file"], p["line"]))
    return entries, problems


def summarize(entries, problems, contract_dir, test_roots):
    active = [e for e in entries if e["status"] == "active"]
    counts = {
        "files": len({e["file"] for e in entries}),
        "obligations": len(active) + sum(e["status"] == "retired" for e in entries),
        "active": len(active),
        "retired": sum(e["status"] == "retired" for e in entries),
        "unconfirmed": sum(e["status"] == "unconfirmed" for e in entries),
        "manual": sum(e["verification"] == "manual" for e in active),
        "tested": sum(e["verification"] == "tested" for e in active),
        "untested": sum(e["verification"] == "untested" for e in active),
        "errors": sum(p["severity"] == "error" for p in problems),
        "warnings": sum(p["severity"] == "warning" for p in problems),
    }
    counts["contract_dir"] = contract_dir
    counts["test_roots"] = test_roots
    return counts


def print_text(summary, problems, strict, failed):
    testable = summary["tested"] + summary["untested"]
    print("Contract: {files} files, {obligations} obligations ({active} active, {retired} retired, "
          "{manual} manual), {unconfirmed} unconfirmed".format(**summary))
    if testable:
        print("Executable: {} of {} testable obligations have tests ({:.0f}%)".format(
            summary["tested"], testable, 100.0 * summary["tested"] / testable))
    print("Searched for tests in: " + (", ".join(summary["test_roots"]) or "nothing"))
    if problems:
        print()
        width = max(len("{}:{}".format(p["file"], p["line"])) for p in problems)
        for p in problems:
            location = "{}:{}".format(p["file"], p["line"])
            print("{:<9} {:<{w}}  {:<9} {}".format(
                p["severity"], location, p["id"] or "", p["message"], w=width))
    print()
    if failed:
        reasons = []
        if summary["errors"]:
            reasons.append("{} errors".format(summary["errors"]))
        if strict and summary["untested"]:
            reasons.append("{} untested".format(summary["untested"]))
        print("FAIL: " + ", ".join(reasons))
    else:
        print("OK" + ("" if strict or not summary["untested"]
                      else " (use --strict to fail on untested obligations)"))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check an IMP Contract: obligation format, unique IDs, and test coverage.")
    parser.add_argument("--contract-dir", default="contract",
                        help="folder holding the Contract (default: contract)")
    parser.add_argument("--tests", nargs="+", metavar="DIR",
                        help="folders to search for tests (default: the usual test folders)")
    parser.add_argument("--all-files", action="store_true",
                        help="search every source file, not only files that look like tests")
    parser.add_argument("--strict", action="store_true",
                        help="also fail when an active obligation has no test")
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.contract_dir):
        print("No Contract folder at '{}'. Start one from the imp-contract templates, "
              "or pass --contract-dir.".format(args.contract_dir), file=sys.stderr)
        return 1

    roots = args.tests or [d for d in DEFAULT_TEST_DIRS if os.path.isdir(d)] or ["."]
    missing = [d for d in roots if not os.path.isdir(d)]
    if missing:
        print("Test folder not found: " + ", ".join(missing), file=sys.stderr)
        return 1
    roots = unique_folders(roots)

    entries, problems = check(args.contract_dir, roots, args.all_files)
    summary = summarize(entries, problems, args.contract_dir, roots)
    failed = bool(summary["errors"]) or (args.strict and summary["untested"] > 0)

    if args.json:
        print(json.dumps({"summary": summary, "obligations": entries, "problems": problems,
                          "ok": not failed}, indent=2))
    else:
        print_text(summary, problems, args.strict, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
