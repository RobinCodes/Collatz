"""
inline_tables.py -- splice the generated tables directly into the paper.

Why this exists.  The paper used to pull its tables in with

    \\input{../Multiverse/data/row_a1.tex}

which is correct on a local TeX run but fails on every online renderer we
tried: they either refuse paths containing `..` or accept only a single
uploaded file, and the error is the unhelpful "file not found".

So the paper is kept as ONE self-contained .tex.  Each table body lives
between a pair of marker comments,

    % >>>BEGIN-DATA row_a1
    ... generated rows ...
    % <<<END-DATA row_a1

and this script refreshes everything between the markers from
``data/<name>.tex``.  Nothing is hand-transcribed, and the paper still
compiles anywhere with no external files.

Run it after generate_data.py:

    python3 generate_data.py && python3 inline_tables.py
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PAPER = os.path.normpath(os.path.join(HERE, "..", "paper",
                                      "collatz_multiverse.tex"))

BEGIN = "% >>>BEGIN-DATA "
END = "% <<<END-DATA "

#: an \input we still recognise, so the one-time conversion is automatic
INPUT_RE = re.compile(
    r"[ \t]*\\input\{(?:\.\./Multiverse/data/|tables/|data/)([A-Za-z0-9_]+)\.tex\}"
    r"(?:[ \t]*\\\\)?[ \t]*\n")


def _body(name: str) -> str:
    """The generated table body, comment header stripped."""
    path = os.path.join(DATA, f"{name}.tex")
    if not os.path.exists(path):
        raise SystemExit(f"missing generated table: {path}\n"
                         f"run generate_data.py first")
    lines = [ln for ln in open(path, encoding="utf-8").read().splitlines()
             if not ln.startswith("%%")]
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def convert_inputs(text: str) -> tuple[str, int]:
    """One-time: turn any surviving \\input into a marker block."""
    count = 0

    def sub(m):
        nonlocal count
        count += 1
        name = m.group(1)
        # grid.tex ships a whole tabular; the row-only tables need the \\
        # that used to sit after the \input restored inside the block.
        tail = "" if name == "grid" else " \\\\"
        return (f"{BEGIN}{name}\n{_body(name)}{tail}\n{END}{name}\n")

    return INPUT_RE.sub(sub, text), count


def refresh(text: str) -> tuple[str, int]:
    """Rewrite the contents of every existing marker block."""
    count = 0
    out = []
    i = 0
    lines = text.splitlines(keepends=True)
    while i < len(lines):
        line = lines[i]
        if line.startswith(BEGIN):
            name = line[len(BEGIN):].strip()
            j = i + 1
            while j < len(lines) and not lines[j].startswith(END + name):
                j += 1
            if j >= len(lines):
                raise SystemExit(f"unterminated data block '{name}'")
            tail = "" if name == "grid" else " \\\\"
            out.append(line)
            out.append(_body(name) + tail + "\n")
            out.append(lines[j])
            count += 1
            i = j + 1
            continue
        out.append(line)
        i += 1
    return "".join(out), count


def main() -> int:
    if not os.path.exists(PAPER):
        raise SystemExit(f"paper not found: {PAPER}")
    text = open(PAPER, encoding="utf-8").read()

    text, converted = convert_inputs(text)
    text, refreshed = refresh(text)

    open(PAPER, "w", encoding="utf-8").write(text)
    print(f"  converted {converted} \\input(s) to inline data blocks")
    print(f"  refreshed {refreshed} data block(s)")
    leftover = INPUT_RE.search(text)
    if leftover:
        print(f"  WARNING: an \\input survived: {leftover.group(0).strip()}")
        return 1
    print(f"  {os.path.relpath(PAPER, HERE)} is now self-contained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
