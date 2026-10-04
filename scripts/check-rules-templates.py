#!/usr/bin/env python3
"""check-rules-templates — the rules templates must number the principles exactly as chapter 03 does.

bootstrap.sh seeds skeleton/CLAUDE.md.template into every new adopter's repo, so a template that
drifts from guide/03-governance-rules.md teaches every adopter a different rule set. It drifted
once: 12 rules against 18 principles, numbered differently, so "Rule 7" meant symmetry in the guide
and deferral in the template (fixed 2026-09-23).

The check: for every `### N. Title` in chapter 03, each template's rule N must open with that same
title in bold. Rules after the last principle are the adopter's own and are not checked.

And the peer-messaging rule (13) must carry the standard's own rules block — PEER-MESSAGING.md §5,
from "(a)" on — word for word, at the standard's version. It drifted once: both templates stamped
"v4" while missing two clauses of the v4 block (fixed 2026-10-04).

    python3 scripts/check-rules-templates.py      # exit 0 in sync · 1 drift (each mismatch listed)
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER = os.path.join(ROOT, "guide", "03-governance-rules.md")
TEMPLATES = [os.path.join(ROOT, "skeleton", "CLAUDE.md.template"),
             os.path.join(ROOT, "skeleton", "AGENTS.md.template")]
STANDARD = os.path.join(ROOT, "skeleton", "peer-messaging", "PEER-MESSAGING.md")
PEER_RULE = 13


def flat(text):
    """Markdown text with blockquote markers and line breaks removed: one line, single spaces."""
    return " ".join(l.lstrip("> ").strip() for l in text.splitlines()).replace("  ", " ").strip()


def standard_block():
    """(version, the §5 rules block from "(a)" to its end), from the standard itself."""
    with open(STANDARD) as f:
        s = f.read()
    ver = re.search(r"^\*\*Version: (\d+)\*\*", s, re.M)
    block = re.search(r"^> \*\*Peer messaging\*\*.*?(?=\n\n)", s, re.M | re.S)
    if not ver or not block:
        return None, None
    text = flat(block.group(0))
    return ver.group(1), text[text.index("(a)"):]


def template_peer_rule(path):
    """(version stamped in rule 13, its text from "(a)" to the rule's end)."""
    with open(path) as f:
        s = f.read()
    m = re.search(rf"^{PEER_RULE}\. \*\*.*?(?=^\d+\. \*\*)", s, re.M | re.S)
    if not m:
        return None, None
    text = flat(m.group(0))
    ver = re.search(r"\*\*v(\d+)\*\*", text)
    return (ver.group(1) if ver else None), (text[text.index("(a)"):] if "(a)" in text else "")


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
    ver, block = standard_block()
    if not block:
        print(f"FAIL: could not read the version and the §5 rules block from {os.path.relpath(STANDARD, ROOT)}")
        bad += 1
    for t in TEMPLATES if block else []:
        tver, ttext = template_peer_rule(t)
        if tver != ver:
            print(f"FAIL: {os.path.relpath(t, ROOT)} rule {PEER_RULE} is stamped v{tver}; the standard is v{ver}")
            bad += 1
        if ttext != block:
            print(f"FAIL: {os.path.relpath(t, ROOT)} rule {PEER_RULE} is not the standard's §5 block, word for word")
            bad += 1
    if bad:
        print(f"\n{bad} mismatch(es). Keep rules 1–{max(want)} in chapter 03's order and titles; "
              "put repo-specific rules after them; rule 13 carries the peer-messaging standard's §5 block.")
        return 1
    print(f"rules templates in sync with chapter 03 ({max(want)} principles, {len(TEMPLATES)} templates) "
          f"and with the peer-messaging standard (v{ver} block)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
