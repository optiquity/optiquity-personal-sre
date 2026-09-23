#!/usr/bin/env python3
"""check-rules-templates — the rules templates must number the principles exactly as chapter 03 does.

bootstrap.sh seeds skeleton/CLAUDE.md.template into every new adopter's repo, so a template that
drifts from guide/03-governance-rules.md teaches every adopter a different rule set. It drifted
once: 12 rules against 18 principles, numbered differently, so "Rule 7" meant symmetry in the guide
and deferral in the template (fixed 2026-09-23).

The check: for every `### N. Title` in chapter 03, each template's rule N must open with that same
title in bold. Rules after the last principle are the adopter's own and are not checked.

    python3 scripts/check-rules-templates.py      # exit 0 in sync · 1 drift (each mismatch listed)
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER = os.path.join(ROOT, "guide", "03-governance-rules.md")
TEMPLATES = [os.path.join(ROOT, "skeleton", "CLAUDE.md.template"),
             os.path.join(ROOT, "skeleton", "AGENTS.md.template")]


def norm(title):
    return " ".join(title.replace("**", "").split()).rstrip(".").strip()


def principles(path):
    with open(path) as f:
        return {int(m.group(1)): norm(m.group(2))
                for m in re.finditer(r"^### (\d+)\. (.+)$", f.read(), re.M)}


def template_rules(path):
    with open(path) as f:
        return {int(m.group(1)): norm(m.group(2))
                for m in re.finditer(r"^(\d+)\. \*\*(.+?)\*\*", f.read(), re.M)}


def main():
    want = principles(CHAPTER)
    if not want or sorted(want) != list(range(1, max(want) + 1)):
        print(f"FAIL: could not read a consecutive list of principles from {CHAPTER}: {sorted(want)}")
        return 1
    bad = 0
    for t in TEMPLATES:
        have = template_rules(t)
        for n, title in sorted(want.items()):
            if have.get(n) != title:
                print(f"FAIL: {os.path.relpath(t, ROOT)} rule {n} is {have.get(n)!r}; chapter 03 says {title!r}")
                bad += 1
    if bad:
        print(f"\n{bad} mismatch(es). Keep rules 1–{max(want)} in chapter 03's order and titles; "
              "put repo-specific rules after them.")
        return 1
    print(f"rules templates in sync with chapter 03 ({max(want)} principles, {len(TEMPLATES)} templates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
