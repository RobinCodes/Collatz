"""
literature.py -- classify the ccchallenge.org corpus and emit the paper's
bibliography appendix.

ccchallenge.org ("The Collatz Conjecture Challenge") maintains a catalogue of
the Collatz literature with the stated aim of formalising it in proof
assistants.  Its public API at /api/papers returns the whole corpus as JSON;
a snapshot is cached in data/ccchallenge_papers.json so this script is
reproducible offline and so the paper's appendix is not hand-transcribed.

    python3 literature.py            # classify the cached snapshot
    python3 literature.py --refresh  # re-download first

Domains are assigned by keyword, first match wins, so each paper appears once.
The ordering of the domain list is therefore significant: the generalised-map
class is tested first because those are the papers this paper actually
engages with.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CACHE = os.path.join(DATA, "ccchallenge_papers.json")
API = "https://ccchallenge.org/api/papers"

DOMAINS = [
    ("generalised maps", [
        r'generali', r'\bqx\s*\+', r'\bqn\s*\+', r'3x\s*\+\s*d', r'3n\s*\+\s*p',
        r'\bax\s*\+\s*b', r'crandall', r'syracuse algorithm', r'analogue',
        r'analog\b', r'variant', r'\bf_q\s*\[x\]', r'polynomial analogue']),
    ("cycles and lower bounds", [r'cycle', r'periodic', r'\bloop', r'perigee']),
    ("stopping time and density", [
        r'stopping time', r'density', r'almost all', r'natural density',
        r'residue']),
    ("computation and verification", [
        r'comput', r'verif', r'search', r'algorithm', r'experimental',
        r'record', r'benchmark']),
    ("logic, automata, formalisation", [
        r'undecidab', r'turing', r'automat', r'formal', r'lean', r'rocq',
        r'isabelle', r'rewriting', r'\bsat\b', r'machine-verified',
        r'busy beaver']),
    ("p-adic, ergodic, analytic", [
        r'\bp-adic', r'2-adic', r'ergodic', r'measure', r'markov',
        r'dynamical', r'fractal', r'analytic', r'entropy']),
    ("surveys and bibliographies", [
        r'bibliograph', r'survey', r'overview', r'unsolved problems',
        r'ultimate challenge']),
]
FALLBACK = "other $3x+1$"

#: titles claiming the whole conjecture.  Listing them is not endorsement;
#: see the note in the appendix.
CLAIM = [r'\bproof of the collatz', r'\bsolution to the collatz',
         r'\bsolving the collatz', r'collatz conjecture is true',
         r'algebraic proof', r'collatz-conjecture proved',
         r'conjecture proved']
#: refereed venues rescue a title that merely sounds like a claim
REFEREED_HINT = [r'journal', r'acta', r'math\. comp', r'monthly', r'proc',
                 r'trans', r'springer', r'lncs', r'colloq', r'advances',
                 r'number theory', r'discrete', r'fibonacci', r'amer']


def load(refresh: bool = False):
    if refresh or not os.path.exists(CACHE):
        import urllib.request
        print(f"  downloading {API} ...")
        with urllib.request.urlopen(API, timeout=90) as r:
            raw = r.read().decode("utf-8")
        os.makedirs(DATA, exist_ok=True)
        open(CACHE, "w", encoding="utf-8").write(raw)
    d = json.load(open(CACHE, encoding="utf-8"))
    return d["items"] if isinstance(d, dict) else d


def blob(i) -> str:
    return " ".join(str(i.get(k) or "") for k in
                    ("title", "abstract", "note", "journal", "booktitle",
                     "venue")).lower()


def classify(items):
    cat = collections.defaultdict(list)
    for i in items:
        b = blob(i)
        for name, pats in DOMAINS:
            if any(re.search(p, b) for p in pats):
                cat[name].append(i)
                break
        else:
            cat[FALLBACK].append(i)
    return cat


def claimed_proofs(items):
    """Titles that claim the whole conjecture, in a venue with no sign of
    refereeing.  Matched on the TITLE only: matching abstracts sweeps in
    legitimate papers that merely contain the word "proof"."""
    out = []
    for i in items:
        b = (i.get("title") or "").lower()
        if not any(re.search(p, b) for p in CLAIM):
            continue
        ven = (i.get("venue") or i.get("journal") or i.get("booktitle") or "")
        if any(re.search(p, ven.lower()) for p in REFEREED_HINT):
            continue          # refereed: not in the unrefereed-claims list
        out.append(i)
    return out


#: bold/italic mathematical alphanumerics and stray typography that appear in
#: a handful of catalogue titles and that pdflatex cannot set
_UNI = {
    "\u2032": "'", "\u2019": "'", "\u2018": "'", "\u201c": "``",
    "\u201d": "''", "\u2013": "--", "\u2014": "---", "\u2212": "-",
    "\u00a0": " ", "\u2026": "...",
}


def _deunicode(s: str) -> str:
    """ASCII-fold a title.  Mathematical alphanumeric symbols (U+1D400..)
    are mapped back to their plain letters/digits; anything else non-ASCII
    that we have no rule for is dropped rather than risking a LaTeX error."""
    out = []
    for ch in s:
        if ch in _UNI:
            out.append(_UNI[ch]); continue
        o = ord(ch)
        if o < 128:
            out.append(ch); continue
        if 0x1D400 <= o <= 0x1D7FF:          # math alphanumerics
            import unicodedata
            nm = unicodedata.normalize("NFKC", ch)
            out.append(nm if nm.isascii() else "")
            continue
        import unicodedata
        nm = unicodedata.normalize("NFKD", ch)
        out.append("".join(c for c in nm if c.isascii()))
    return "".join(out)


#: maths macros we are willing to pass through to LaTeX untouched.  The paper
#: loads amsmath/amssymb, so all of these typeset; anything outside the list is
#: reduced to its bare letters as before, which is safe but lossy.
_MATH_OK = set(r"""
alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa
lambda mu nu xi pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi
psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega
leq geq le ge neq ne equiv approx sim simeq cong propto ll gg pm mp times cdot
div ast star circ bullet oplus otimes cap cup setminus subset subseteq supset
supseteq in notin ni forall exists infty partial nabla emptyset
to rightarrow leftarrow mapsto Rightarrow Leftarrow leftrightarrow
Leftrightarrow ldots cdots dots vdots ddots prime ell Re Im aleph
pmod bmod mod gcd lcm max min sup inf lim limsup liminf log ln exp sin cos tan
deg dim ker det frac sqrt sum prod int oint bigcup bigcap
left right big Big bigg Bigg langle rangle lfloor rfloor lceil rceil
mathbb mathbf mathcal mathrm mathit mathsf mathtt text operatorname hbox mbox
overline underline widehat hat tilde bar vec dot ddot pounds quad qquad
""".split())

_KEEP = "\x01"          # sentinel wrapping a whitelisted macro name


def _math_reduce(seg: str) -> str:
    r"""Last-resort flattening of a maths segment: every macro becomes its own
    letters and all grouping disappears.  Used only when the segment cannot be
    passed through safely (unbalanced braces)."""
    seg = re.sub(r"\\(?:mathbb|mathbf|mathcal|mathrm|mathit|mathsf|text"
                 r"|operatorname|hbox|mbox)\s*\{([^{}]*)\}", r"\1", seg)
    seg = re.sub(r"\\([a-zA-Z]+)\s*", r"\1 ", seg)
    return seg.replace("{", "").replace("}", "").replace("\\", "")


def _math_pass(seg: str) -> str:
    r"""Typeset a maths segment, keeping the macros we recognise.

    An earlier version deleted every backslash here, which turned
    "$m \leq 91$" into "$m leq 91$" and "$\pounds$" into "$pounds$" in the
    printed bibliography.  Now a whitelisted macro survives verbatim and only
    an unrecognised one is flattened to its letters.
    """
    if seg.count("{") != seg.count("}"):
        return _math_reduce(seg)
    kept = re.sub(r"\\([a-zA-Z]+)",
                  lambda m: (_KEEP + m.group(1) + _KEEP
                             if m.group(1) in _MATH_OK else m.group(0)),
                  seg)
    # anything still carrying a backslash is a macro we do not vouch for
    kept = re.sub(r"\\([a-zA-Z]+)\s*", r"\1 ", kept)
    # the sentinels stay in place: tex_escape strips every remaining backslash
    # from the whole string a few lines further on, so the whitelisted macros
    # can only be restored once that has happened.
    return kept.replace("\\", "")


def tex_escape(s: str) -> str:
    r"""Make a catalogue title safe to typeset.

    Titles arrive as BibTeX fragments, so they mix plain text with maths and
    assume packages we cannot know.  The strategy is to keep $...$ segments as
    maths, passing through the macros of `_MATH_OK` and reducing any other
    macro to plain letters.  Literal escaped dollars (prices!) are protected
    first, since otherwise they are mistaken for maths delimiters.
    """
    SENT = "\x00DOLLAR\x00"
    s = _deunicode(s).replace(r"\$", SENT)

    parts = s.split("$")
    for k in range(1, len(parts), 2):                 # maths segments
        parts[k] = _math_pass(parts[k])
    # a macro-only segment may now be empty; drop the delimiters rather than
    # emitting "$$", which LaTeX reads as display maths
    out = [parts[0]]
    for k in range(1, len(parts), 2):
        seg = parts[k]
        tail = parts[k + 1] if k + 1 < len(parts) else ""
        out.append(f"${seg}$" if seg.strip() else "")
        out.append(tail)
    s = "".join(out)

    s = s.replace("\\", " ").replace("&", r"\&").replace("%", r"\%")
    s = s.replace("#", r"\#")                     # valid in text and in maths
    # underscores are subscripts inside maths and must not be escaped there
    parts = s.split("$")
    for k in range(0, len(parts), 2):
        parts[k] = parts[k].replace("_", r"\_")
    s = "$".join(parts)

    if s.count("$") % 2:
        s += "$"
    parts = s.split("$")
    for k in range(0, len(parts), 2):
        parts[k] = parts[k].replace("^", r"\^{}").replace("~",
                                                          r"\textasciitilde{}")
    s = "$".join(parts).replace(SENT, r"\$")
    return re.sub(_KEEP + r"([a-zA-Z]+)" + _KEEP, r"\\\1 ", s)


#: lowercase nobiliary particles that belong to the surname
_PARTICLES = {"van", "von", "de", "del", "della", "der", "den", "da", "di",
              "du", "la", "le", "ten", "ter"}


def _surnames(field: str) -> list:
    r"""Every surname in a BibTeX-ish author field, in order.

    Three conventions appear in the catalogue and all three must be handled:

        "Ethan Akin"                          First Last
        "Zarnowski, Roger E."                 Last, First
        "Wang, X.; Wang, Q.; and Xu, Z."      semicolon-separated Last, First
        "R. Blecksmith, M. McCallum, and J. Selfridge"   comma-separated list

    Splitting on every comma -- which an earlier version did -- turned
    "Zarnowski, Roger E." into two authors and printed "Zarnowski \& E.".
    The discriminator is what sits *before* the comma: a single token (plus
    any nobiliary particle) means "Last, First"; anything longer means the
    comma is separating whole names.
    """
    out = []
    for group in field.split(";"):
        for frag in re.split(r"\s+and\s+", group.strip()):
            frag = re.sub(r"^and\s+", "", frag.strip()).strip().strip(",")
            if not frag or frag.lower().startswith("et al"):
                continue
            head = frag.split(",", 1)[0].strip()
            toks = head.split()
            inverted = ("," in frag and toks
                        and (len(toks) == 1
                             or all(t.lower() in _PARTICLES
                                    for t in toks[:-1])))
            if inverted:
                out.append(head)
            else:
                for one in frag.split(","):
                    one = one.strip()
                    if one:
                        out.append(one.split()[-1])
    return out


def short_authors(a: str) -> str:
    """Surname, "X \\& Y" or "X et al." for a catalogue author field."""
    names = _surnames(a or "")
    if not names:
        return "?"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return names[0] + " \\& " + names[1]
    return names[0] + " et al."


def emit(items, cat, claims):
    order = [n for n, _ in DOMAINS] + [FALLBACK]

    # ---- domain counts table ----
    rows = [r"%s & %d \\" % (n.replace("$3x+1$", r"other $3x+1$") if False else n,
                             len(cat[n])) for n in order]
    rows.append(r"\midrule \textbf{total} & \textbf{%d} \\" % len(items))
    open(os.path.join(DATA, "lit_domains.tex"), "w", encoding="utf-8").write(
        "%% generated by literature.py -- do not edit\n" + "\n".join(rows) + "\n")

    # ---- the generalised-map class, listed in full ----
    gen = sorted(cat["generalised maps"], key=lambda i: (i.get("year", ""),
                                                         i.get("authors", "")))
    lines = [r"\textit{%s} (%s) & %s \\" %
             (tex_escape(short_authors(i["authors"])), i.get("year", "?"),
              tex_escape(i["title"]))
             for i in gen]
    open(os.path.join(DATA, "lit_generalised.tex"), "w", encoding="utf-8").write(
        "%% generated by literature.py -- do not edit\n" + "\n".join(lines) + "\n")

    # ---- the whole corpus, compact ----
    allp = sorted(items, key=lambda i: (i.get("authors", ""), i.get("year", "")))
    dom_of = {}
    for n in order:
        for i in cat[n]:
            dom_of[i["bibtex_key"]] = n
    lines = []
    for i in allp:
        d = dom_of.get(i["bibtex_key"], FALLBACK)
        tag = {"generalised maps": "G", "cycles and lower bounds": "C",
               "stopping time and density": "D",
               "computation and verification": "V",
               "logic, automata, formalisation": "L",
               "p-adic, ergodic, analytic": "P",
               "surveys and bibliographies": "S"}.get(d, "-")
        t = _deunicode(i["title"])
        if len(t) > 68:
            t = t[:66].rstrip()
            if t.count("$") % 2:
                # the cut landed inside maths.  Closing it with a bare "$"
                # would leave a half-written macro ("$\\mathbb$"), so drop the
                # incomplete fragment instead.
                t = t[:t.rfind("$")].rstrip()
            t += " ..."
        lines.append(r"%s & %s & %s & %s \\" %
                     (tag, tex_escape(short_authors(i["authors"])),
                      i.get("year", "?"), tex_escape(t)))
    open(os.path.join(DATA, "lit_corpus.tex"), "w", encoding="utf-8").write(
        "%% generated by literature.py -- do not edit\n" + "\n".join(lines) + "\n")

    # ---- inline figures the paper quotes about the corpus ----
    facts = [r"\newcommand{\FactCorpusN}{%d}" % len(allp),
             r"\newcommand{\FactCorpusGen}{%d}"
             % len(cat.get("generalised maps", [])),
             r"\newcommand{\FactCorpusClaims}{%d}" % len(claims)]
    open(os.path.join(DATA, "litfacts.tex"), "w", encoding="utf-8").write(
        "%% generated by literature.py -- do not edit\n" + "\n".join(facts) + "\n")

    # ---- plain text report ----
    rep = ["ccchallenge.org corpus, classified", "=" * 74, "",
           f"snapshot: {len(items)} papers", ""]
    for n in order:
        rep.append(f"{n:<32} {len(cat[n]):>4}")
    rep += ["", f"claimed complete proofs without a refereed venue: {len(claims)}",
            "(listed without endorsement; none is formalised on ccchallenge)"]
    for i in sorted(claims, key=lambda x: x.get("year", "")):
        rep.append(f"  {i.get('year','?'):<12} {i['authors'][:34]:<34} {i['title'][:58]}")
    rep += ["", "generalised-map class (the multiverse-relevant papers):"]
    for i in gen:
        rep.append(f"  {i.get('year','?'):<6} {i['authors'][:36]:<36} {i['title'][:70]}")
    open(os.path.join(DATA, "literature.txt"), "w", encoding="utf-8").write(
        "\n".join(rep) + "\n")

    print(f"  {len(items)} papers, {len(gen)} in the generalised-map class, "
          f"{len(claims)} unrefereed proof claims")
    for f in ("lit_domains.tex", "lit_generalised.tex", "lit_corpus.tex",
              "litfacts.tex", "literature.txt"):
        print(f"  wrote data/{f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    items = load(args.refresh)
    cat = classify(items)
    emit(items, cat, claimed_proofs(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
