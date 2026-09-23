#!/usr/bin/env python3
"""check-guide-links — the guide's cross-references must point where they say they point.

This repo is densely cross-linked and has been renumbered, and a renumbering leaves three kinds of
damage a filename-only sweep misses. Four checks, over every tracked text file:

  1. LINKS   every relative markdown link resolves to a file that exists (anchors not checked).
  2. LABELS  a link whose label starts with a chapter number points to THAT chapter:
             [14 · Sharing](19-sharing.md) is wrong even though the file exists.
  3. NAMES   a chapter file named in plain text — a code comment, a template header,
             "see guide/09-permissions.md" — exists. Plain text is not a link, so no link check sees it.
  4. NEXT    the reading order holds: each chapter ends with a "Next:" line whose first link is the
             next chapter (or, for a chapter with case studies, its first case study); a case study's
             points to its next sibling case study, or back to the next main chapter.

    python3 scripts/check-guide-links.py      # exit 0 clean · 1 problems (each listed with file:line)
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = os.path.join(ROOT, "guide")
TEXT = (".md", ".template", ".example", ".json", ".toml", ".yml", ".yaml", ".sh", ".hook", ".py", ".conf", "")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
CHAPTER = re.compile(r"^(\d{2})([a-z]?)-")
NAMED = re.compile(r"(?<![\w/.-])(?:guide/)?(\d{2}[a-z]?-[a-z0-9-]+)\.md\b")


def tracked():
    out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True, check=True).stdout
    # CHANGELOG.md is history: it quotes the old, broken references on purpose to say what changed.
    skip = ("scripts/check-guide-links", "CHANGELOG.md")
    return [f for f in out.splitlines() if os.path.splitext(f)[1] in TEXT and not f.startswith(skip)]


def chapters():
    return sorted(f for f in os.listdir(GUIDE) if CHAPTER.match(f) and f.endswith(".md"))


def expected_next(files):
    """{chapter: set of acceptable first links for its Next: line}."""
    exp = {}
    mains = [f for f in files if not CHAPTER.match(f).group(2)]
    for f in files:
        num, letter = CHAPTER.match(f).groups()
        later_mains = [m for m in mains if m > f and CHAPTER.match(m).group(1) > num]
        next_main = later_mains[0] if later_mains else None
        siblings = [c for c in files if CHAPTER.match(c).group(1) == num and CHAPTER.match(c).group(2)]
        if letter:                                   # a case study: next sibling, else the next main
            later_sibs = [s for s in siblings if s > f]
            want = {later_sibs[0]} if later_sibs else ({next_main} if next_main else set())
        else:                                        # a main chapter: the next main, or its first case study
            want = ({next_main} if next_main else set()) | ({siblings[0]} if siblings else set())
        if want:
            exp[f] = want
    return exp


def main():
    problems = []
    files = chapters()
    for rel in tracked():
        path = os.path.join(ROOT, rel)
        try:
            lines = open(path, encoding="utf-8").read().splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        base = os.path.dirname(path)
        for n, line in enumerate(lines, 1):
            for label, target in LINK.findall(line):
                if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                    continue
                t = target.split("#", 1)[0]
                if t and rel.endswith(".md") and not os.path.exists(os.path.normpath(os.path.join(base, t))):
                    problems.append(f"{rel}:{n}: LINK   {target} does not exist")
                m = re.match(r"^\s*(\d{2}[a-z]?)\b", label)
                tb = os.path.basename(t)
                if m and CHAPTER.match(tb) and not tb.startswith(m.group(1) + "-"):
                    problems.append(f"{rel}:{n}: LABEL  [{label}] points to {tb}")
            for name in NAMED.findall(line):
                if not os.path.exists(os.path.join(GUIDE, name + ".md")):
                    problems.append(f"{rel}:{n}: NAME   {name}.md — no such chapter")
    for f, want in expected_next(files).items():
        lines = open(os.path.join(GUIDE, f), encoding="utf-8").read().splitlines()
        nxt = [(n, l) for n, l in enumerate(lines, 1) if re.match(r"^\s*\**Next:?\**:?\s", l) or l.startswith("Next:")]
        if not nxt:
            problems.append(f"guide/{f}: NEXT   no 'Next:' line (expected {' or '.join(sorted(want))})")
            continue
        n, l = nxt[-1]
        first = LINK.search(l)
        got = os.path.basename(first.group(2).split("#", 1)[0]) if first else None
        if got not in want:
            problems.append(f"guide/{f}:{n}: NEXT   points to {got}; expected {' or '.join(sorted(want))}")
    for p in problems:
        print(p)
    print(f"\n{len(problems)} problem(s)" if problems else f"guide links, labels, names and reading order OK ({len(files)} chapters)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
