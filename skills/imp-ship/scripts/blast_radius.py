#!/usr/bin/env python3
"""Estimate a change's blast radius from its diff: low, medium, high, or catastrophic.

The result is a floor based on what the diff touches. Raise it when the code's meaning
warrants; only a human may lower it.

Signals:
  * paths: secrets and key files, migrations, auth, money, infrastructure and CI, public
    schemas, ownership rules, dependencies, other source, and docs and tests;
  * added lines: possible secrets, and destructive data changes;
  * size: large diffs of source code;
  * the Contract: obligations added, changed, removed, or retired.

The diff runs from the merge base with --base to the working tree, so it includes
uncommitted and untracked files.

Usage:
  python3 blast_radius.py [--base REF] [--contract-dir contract]
                          [--catastrophic GLOB] [--high GLOB] [--medium GLOB] [--low GLOB]
                          [--fail-above LEVEL] [--json]

Globs use / separators; ** matches any number of folders; a glob without / matches the
file name in any folder. Repeat a flag to add globs. --low wins over everything, and
catastrophic globs apply even to docs and tests. Other globs apply to the remaining files
and add to the defaults; a path takes the highest level it matches.

Exit status is 1 when --fail-above is given and the level is above it, 2 when git fails,
and 0 otherwise.
"""

import argparse
import json
import os
import re
import subprocess
import sys

LEVELS = ["low", "medium", "high", "catastrophic"]
GATES = {
    "low": "Green checks and a clean adversarial review, then auto-merge.",
    "medium": "As low, plus release behind a canary or flag; a human reads the Contract "
              "diff if obligations changed.",
    "high": "A human reviews the Contract diff and the rollout plan, and reads code only "
            "where they choose.",
    "catastrophic": "A human reviews code, Contract, and rollout; rehearse the rollback; "
                    "never auto-merge.",
}

DEFAULT_CATASTROPHIC = [
    ("secret or key file", ["*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore",
                            "id_rsa", "id_ecdsa", "id_ed25519", ".env", ".env.local",
                            ".env.production", "*.tfstate", "*.tfstate.backup"]),
]
DEFAULT_RULES = [
    ("high", "database migration or schema",
     ["**/migrations/**", "**/migrate/**", "*.sql", "schema.rb", "*.prisma",
      "**/liquibase/**", "**/flyway/**"]),
    ("high", "authentication, authorization, or security",
     ["**/auth/**", "**/authn/**", "**/authz/**", "**/authentication/**",
      "**/authorization/**", "**/security/**", "**/permissions/**", "*permission*",
      "*entitlement*", "*crypto*", "*encrypt*", "*secret*", "*credential*", "*password*",
      "*oauth*"]),
    ("high", "money",
     ["*payment*", "*billing*", "*ledger*", "*invoice*", "*checkout*", "*refund*",
      "*payout*", "*wallet*"]),
    ("high", "infrastructure, deploy, or CI",
     [".github/workflows/**", ".github/actions/**", ".gitlab-ci.yml", ".circleci/**",
      ".buildkite/**", "Jenkinsfile", "Dockerfile", "*.dockerfile", "docker-compose*.yml",
      "docker-compose*.yaml", "*.tf", "*.tfvars", "**/terraform/**", "**/k8s/**",
      "**/kubernetes/**", "**/helm/**", "**/charts/**", "**/infra/**", "**/deploy/**",
      "fastlane/**", "Fastfile"]),
    ("high", "public interface or schema",
     ["*openapi*.yaml", "*openapi*.yml", "*openapi*.json", "*swagger*.yaml",
      "*swagger*.yml", "*swagger*.json", "*.proto", "*.graphql", "*.graphqls", "*.avsc"]),
    ("high", "review and ownership rules", ["CODEOWNERS"]),
    ("medium", "dependencies",
     ["package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
      "Gemfile", "Gemfile.lock", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
      "requirements*.txt", "pyproject.toml", "poetry.lock", "uv.lock", "Pipfile",
      "Pipfile.lock", "Podfile", "Podfile.lock", "Package.swift", "Package.resolved",
      "Cartfile", "Cartfile.resolved", "build.gradle", "build.gradle.kts", "settings.gradle",
      "settings.gradle.kts", "gradle.properties", "libs.versions.toml", "pom.xml",
      "*.csproj", "packages.config", "Directory.Packages.props", "composer.json",
      "composer.lock", "mix.exs", "mix.lock"]),
]
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "Gemfile.lock",
             "go.sum", "Cargo.lock", "poetry.lock", "uv.lock", "Pipfile.lock", "Podfile.lock",
             "Package.resolved", "Cartfile.resolved", "composer.lock", "mix.lock"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc"}
TEST_DIR_NAMES = {"test", "tests", "spec", "specs", "__tests__", "e2e", "fixtures"}

STRONG_SECRETS = [
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED |PGP )?"
                               r"PRIVATE KEY")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
]
ASSIGNED_SECRET = re.compile(
    r"(?i)\b(?:api[_-]?key|secret|password|passwd|private[_-]?key|access[_-]?token|"
    r"auth[_-]?token|client[_-]?secret)\b['\"]?\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")
DESTRUCTIVE = re.compile(
    r"(?i)\bDROP\s+(?:TABLE|COLUMN|DATABASE|SCHEMA)\b|\bTRUNCATE\s+(?:TABLE\s+)?\w"
    r"|\bALTER\s+TABLE\s+\S+\s+DROP\b|\bdrop_table\b|\bremove_column\b|\bdropTable\b"
    r"|\bdropColumn\b|\bRemoveField\b|\bDeleteModel\b|<drop(?:Table|Column)\b")

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
OBLIGATION = re.compile(r"^([A-Z][A-Z0-9]{1,9}-\d{3,})[:.,]?(?:\s+\[([^\]]*)\])?")
FENCE = re.compile(r"^\s*(```|~~~)")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class GitError(Exception):
    pass


def git(*args):
    result = subprocess.run(["git", "-c", "core.quotepath=off"] + list(args),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise GitError(result.stderr.decode("utf-8", "replace").strip()
                       or "git " + " ".join(args) + " failed")
    return result.stdout.decode("utf-8", "replace")


def glob_regex(pattern):
    if "/" not in pattern:
        pattern = "**/" + pattern
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile("^" + out + "$", re.I)


def compile_rules(rules):
    return [(level, why, [glob_regex(g) for g in globs]) for level, why, globs in rules]


def match_rules(path, rules):
    best = None
    for level, why, patterns in rules:
        if any(p.match(path) for p in patterns):
            if best is None or LEVELS.index(level) > LEVELS.index(best[0]):
                best = (level, why)
    return best


def is_test_path(path):
    parts = path.split("/")
    for directory in parts[:-1]:
        if directory.lower() in TEST_DIR_NAMES or directory.endswith(("Tests", "Test")):
            return True
    name = parts[-1]
    lowered = name.lower()
    stem = name.split(".")[0]
    return (lowered.startswith("test_")
            or re.search(r"[._-](test|spec)s?\.", lowered) is not None
            or re.search(r"(Test|Tests|Spec|IT)$", stem) is not None)


def is_doc_path(path):
    if os.path.basename(path) == "CODEOWNERS":
        return False
    return (os.path.splitext(path)[1].lower() in DOC_EXTENSIONS
            or path.split("/")[0].lower() in ("docs", "doc"))


def resolve_base(base):
    if base:
        return base
    try:
        return git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD").strip()
    except GitError:
        pass
    for candidate in ("origin/main", "origin/master", "main", "master"):
        try:
            git("rev-parse", "--verify", "--quiet", candidate + "^{commit}")
            return candidate
        except GitError:
            continue
    raise GitError("can't find a base branch; pass --base")


def parse_diff(text):
    files, current, in_header, old_line, new_line = {}, None, False, 0, 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            current, in_header = None, True
        elif in_header and line.startswith("--- "):
            old_path = line[4:]
            current = {"old": None if old_path == "/dev/null" else old_path[2:],
                       "added": [], "removed": []}
        elif in_header and line.startswith("+++ ") and current is not None:
            new_path = line[4:]
            current["new"] = None if new_path == "/dev/null" else new_path[2:]
            files[current["new"] or current["old"]] = current
        elif line.startswith("@@") and current is not None:
            in_header = False
            match = HUNK.match(line)
            if match:
                old_line, new_line = int(match.group(1)), int(match.group(3))
        elif in_header:
            continue
        elif current is not None and line.startswith("+"):
            current["added"].append((new_line, line[1:]))
            new_line += 1
        elif current is not None and line.startswith("-"):
            current["removed"].append((old_line, line[1:]))
            old_line += 1
    return files


def obligation_lines(text):
    by_line, kinds, current, in_fence = {}, {}, None, False
    for number, line in enumerate((text or "").splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
        heading = None if in_fence else HEADING.match(line)
        if heading and len(heading.group(1)) <= 3:
            current = None
            found = OBLIGATION.match(heading.group(2)) if len(heading.group(1)) == 3 else None
            if found:
                current = found.group(1)
                kinds[current] = (found.group(2) or "").strip().lower()
        if current:
            by_line[number] = current
    return by_line, kinds


def contract_changes(merge_base, diff_files, contract_dir):
    prefix = contract_dir.strip("/") + "/"
    old_kinds, new_kinds, touched = {}, {}, set()
    for path, entry in diff_files.items():
        if not path.startswith(prefix) or not path.lower().endswith(".md"):
            continue
        old_text = ""
        if entry["old"]:
            try:
                old_text = git("show", "{}:{}".format(merge_base, entry["old"]))
            except GitError:
                old_text = ""
        new_text = ""
        if entry.get("new") and os.path.isfile(entry["new"]):
            with open(entry["new"], encoding="utf-8", errors="replace") as handle:
                new_text = handle.read()
        old_map, kinds = obligation_lines(old_text)
        old_kinds.update(kinds)
        new_map, kinds = obligation_lines(new_text)
        new_kinds.update(kinds)
        touched.update(old_map[n] for n, _ in entry["removed"] if n in old_map)
        touched.update(new_map[n] for n, _ in entry["added"] if n in new_map)
    result = {"added": [], "changed": [], "removed": [], "retired": []}
    for obligation in sorted(touched | (set(new_kinds) ^ set(old_kinds))):
        if obligation not in old_kinds:
            result["retired" if new_kinds.get(obligation) == "retired" else "added"].append(
                obligation)
        elif obligation not in new_kinds:
            result["removed"].append(obligation)
        elif new_kinds[obligation] == "retired" and old_kinds[obligation] != "retired":
            result["retired"].append(obligation)
        else:
            result["changed"].append(obligation)
    return result


def assess(base, contract_dir, team_low, team_rules):
    base = resolve_base(base)
    merge_base = git("merge-base", base, "HEAD").strip()
    numstat = git("diff", "--numstat", "--no-renames", merge_base)
    diff_files = parse_diff(git("diff", "-U0", "--no-color", "--no-renames", merge_base))

    stats = {}
    for line in numstat.splitlines():
        added, deleted, path = line.split("\t", 2)
        stats[path] = (int(added) if added.isdigit() else 0,
                       int(deleted) if deleted.isdigit() else 0)
    for path in git("ls-files", "--others", "--exclude-standard").splitlines():
        lines = []
        try:
            if os.path.getsize(path) <= 1000000:
                with open(path, "rb") as handle:
                    raw = handle.read()
                if b"\0" not in raw:
                    lines = raw.decode("utf-8", "replace").splitlines()
        except OSError:
            pass
        stats[path] = (len(lines), 0)
        diff_files[path] = {"old": None, "new": path, "removed": [],
                            "added": list(enumerate(lines, start=1))}

    low_patterns = [glob_regex(g) for g in team_low]
    team_catastrophic = compile_rules([r for r in team_rules if r[0] == "catastrophic"])
    team = compile_rules([r for r in team_rules if r[0] != "catastrophic"])
    catastrophic = compile_rules([("catastrophic", why, globs)
                                  for why, globs in DEFAULT_CATASTROPHIC])
    defaults = compile_rules(DEFAULT_RULES)

    reasons, source_lines, quiet = [], 0, 0
    for path in sorted(stats):
        added, deleted = stats[path]
        hit = None
        if any(p.match(path) for p in low_patterns):
            hit = ("low", "team low-risk path")
        hit = hit or match_rules(path, team_catastrophic + catastrophic)
        if hit is None and is_doc_path(path):
            hit = ("low", "docs")
        if hit is None and is_test_path(path):
            hit = ("low", "tests")
        hit = hit or match_rules(path, team + defaults) or ("medium", "source or asset change")
        if hit[0] == "low":
            quiet += 1
        else:
            reasons.append({"level": hit[0], "path": path, "rule": hit[1]})
        test_or_doc = hit[1] in ("docs", "tests", "team low-risk path")
        if not test_or_doc and os.path.basename(path) not in LOCKFILES:
            source_lines += added + deleted

        for number, text in diff_files.get(path, {}).get("added", []):
            for name, pattern in STRONG_SECRETS:
                if pattern.search(text):
                    reasons.append({"level": "catastrophic", "path": path, "line": number,
                                    "rule": "possible secret: " + name})
            if test_or_doc:
                continue
            if ASSIGNED_SECRET.search(text):
                reasons.append({"level": "catastrophic", "path": path, "line": number,
                                "rule": "possible hard-coded secret"})
            found = DESTRUCTIVE.search(text)
            if found:
                reasons.append({"level": "catastrophic", "path": path, "line": number,
                                "rule": "destructive data change: " + found.group(0)})

    if source_lines > 1000:
        reasons.append({"level": "high", "path": "(diff)",
                        "rule": "{} changed source lines: hard to reason about, split it "
                                "if you can".format(source_lines)})
    elif source_lines > 400 or len(stats) - quiet > 30:
        reasons.append({"level": "medium", "path": "(diff)",
                        "rule": "large diff: {} source lines across {} files".format(
                            source_lines, len(stats) - quiet)})

    contract = contract_changes(merge_base, diff_files, contract_dir)
    for kind, level in (("removed", "high"), ("retired", "high"), ("changed", "medium")):
        if contract[kind]:
            reasons.append({"level": level, "path": contract_dir,
                            "rule": "obligations {}: {}".format(kind, ", ".join(contract[kind]))})

    level = "low"
    for reason in reasons:
        if LEVELS.index(reason["level"]) > LEVELS.index(level):
            level = reason["level"]
    reasons.sort(key=lambda r: (-LEVELS.index(r["level"]), r["path"], r.get("line", 0)))
    return {
        "level": level,
        "base": base,
        "merge_base": merge_base,
        "files": len(stats),
        "added": sum(a for a, _ in stats.values()),
        "deleted": sum(d for _, d in stats.values()),
        "low_risk_files": quiet,
        "reasons": reasons,
        "contract": contract,
        "contract_review": any(contract.values()),
        "default_gate": GATES[level],
    }


def print_text(result):
    print("Blast radius: {} (a floor: raise it if the code's meaning warrants; only a human "
          "may lower it)".format(result["level"]))
    print("Base: {} (merge base {}), {} files, +{} -{} lines".format(
        result["base"], result["merge_base"][:10], result["files"], result["added"],
        result["deleted"]))
    if result["reasons"]:
        print()
        width = max(len(r["path"] + (":{}".format(r["line"]) if "line" in r else ""))
                    for r in result["reasons"])
        for r in result["reasons"]:
            where = r["path"] + (":{}".format(r["line"]) if "line" in r else "")
            print("  {:<12}  {:<{w}}  {}".format(r["level"], where, r["rule"], w=width))
    if result["low_risk_files"]:
        print("  {:<12}  {} docs, test, or team low-risk files".format(
            "low", result["low_risk_files"]))
    contract = result["contract"]
    if result["contract_review"]:
        parts = ["{} {}".format(kind, ", ".join(ids)) for kind, ids in contract.items() if ids]
        print()
        print("Contract: " + "; ".join(parts))
    print()
    print("Default gate: " + result["default_gate"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Estimate a change's blast radius.")
    parser.add_argument("--base", help="branch the change merges into (default: origin's "
                                       "default branch)")
    parser.add_argument("--contract-dir", default="contract",
                        help="IMP Contract folder (default: contract)")
    for level in ("catastrophic", "high", "medium"):
        parser.add_argument("--" + level, action="append", default=[], metavar="GLOB",
                            help="team path that is at least {}".format(level))
    parser.add_argument("--low", action="append", default=[], metavar="GLOB",
                        help="team path that is low risk; wins over every other rule")
    parser.add_argument("--fail-above", choices=LEVELS, metavar="LEVEL",
                        help="exit 1 when the level is above LEVEL")
    parser.add_argument("--json", action="store_true", help="print machine-readable output")
    args = parser.parse_args(argv)

    team_rules = [(level, "team {} path".format(level), getattr(args, level))
                  for level in ("catastrophic", "high", "medium") if getattr(args, level)]
    try:
        result = assess(args.base, args.contract_dir, args.low, team_rules)
    except GitError as error:
        print("git failed: {}".format(error), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    if args.fail_above and LEVELS.index(result["level"]) > LEVELS.index(args.fail_above):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
