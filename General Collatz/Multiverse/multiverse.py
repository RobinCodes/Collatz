"""
multiverse.py -- structure theory of the generalised Collatz maps

    T_{a,b}(n) = n / 2        if n is even
                 a*n + b      if n is odd

This module is the computational counterpart of the paper

    "The Generalised Collatz Multiverse: Symmetries, Reductions and Fates
     of the maps  n -> n/2 (even),  n -> a n + b (odd)"

(../paper/collatz_multiverse.tex).  It is a pure-stdlib library -- no numpy,
no matplotlib -- so that it can be imported by the Tk GUI, by the data
generator, and from a bare REPL alike.

The three things it knows how to do:

  1. CLASSIFY a universe (a, b): decide which of the solved families it lies
     in, or certify it as genuinely open.  See `classify`.

  2. REDUCE a universe along the two symmetries of the family:
       * the halving symmetry     (2a, 2b)  ~  (a, b)
       * the odd-scaling symmetry  d * T_{a,b}  =  T_{a,db} | dZ    (d odd)
     and report the normal form, which is always coprime.  See `normal_form`.

  3. CENSUS the cycles of a universe and split them along the divisor
     decomposition theorem.  See `find_cycles` and `decompose_cycles`.

Everything here is exact integer arithmetic; Python ints are unbounded, so
there are no overflow caveats.

Author: RobinCodes.  Written with AI assistance; see the paper's note on the
use of artificial intelligence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "Fate",
    "Family",
    "Knowledge",
    "knowledge",
    "Universe",
    "Cycle",
    "step",
    "orbit",
    "classify",
    "normal_form",
    "reduction_chain",
    "attracting_primes",
    "repelling_primes",
    "sub_universes",
    "find_cycles",
    "decompose_cycles",
    "cycle_equation_residual",
    "drift",
    "radical",
    "one_is_periodic",
    "half_line_invariance",
    "reduces_to_offset_one",
    "grid",
    "growth_statistics",
]


# ======================================================================
# 1.  Elementary number theory helpers
# ======================================================================

def v2(n: int) -> int:
    """2-adic valuation.  v2(0) is treated as +infinity (returned as -1
    sentinel is error-prone, so we raise instead; callers guard on n != 0)."""
    if n == 0:
        raise ValueError("v2(0) is undefined (infinite)")
    n = abs(n)
    return (n & -n).bit_length() - 1


def vp(n: int, p: int) -> int:
    """p-adic valuation of a nonzero integer."""
    if n == 0:
        raise ValueError("vp(0) is undefined (infinite)")
    n = abs(n)
    e = 0
    while n % p == 0:
        n //= p
        e += 1
    return e


def odd_part(n: int) -> int:
    """Largest odd divisor of n != 0."""
    if n == 0:
        raise ValueError("odd_part(0) is undefined")
    n = abs(n)
    while n % 2 == 0:
        n //= 2
    return n


def factorise(n: int) -> Dict[int, int]:
    """Trial-division factorisation.  Inputs here are small (map parameters),
    so trial division is ample."""
    n = abs(n)
    out: Dict[int, int] = {}
    if n <= 1:
        return out
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def odd_divisors(n: int) -> List[int]:
    """All positive odd divisors of n != 0, ascending."""
    if n == 0:
        raise ValueError("odd_divisors(0) is undefined")
    m = odd_part(n)
    out = [d for d in range(1, m + 1) if m % d == 0]
    return out


# ======================================================================
# 2.  The map itself
# ======================================================================

def step(n: int, a: int, b: int) -> int:
    """One application of T_{a,b}."""
    return n // 2 if n % 2 == 0 else a * n + b


def orbit(n: int, a: int, b: int, max_steps: int = 10_000,
          value_cap: Optional[int] = None) -> Tuple[List[int], Optional[int]]:
    """Iterate T_{a,b} from n.

    Returns (trajectory, cycle_start_index).  `cycle_start_index` is None if
    no repeat was seen before the step or value budget ran out; otherwise
    trajectory[cycle_start_index:] is one full period.
    """
    seen: Dict[int, int] = {}
    traj: List[int] = []
    for i in range(max_steps):
        if n in seen:
            return traj, seen[n]
        if value_cap is not None and abs(n) > value_cap:
            return traj, None
        seen[n] = i
        traj.append(n)
        n = step(n, a, b)
    return traj, None


# ======================================================================
# 3.  Classification
# ======================================================================

class Fate:
    """Fate of *every* orbit of a universe, over the positive integers."""
    CYCLIC = "all orbits eventually periodic"       # proved
    DIVERGENT = "all orbits diverge"                # proved
    TERMINAL = "all orbits reach a fixed point"     # proved (a = b = 0)
    OPEN = "open"                                   # unresolved

    #: fates for which a complete proof is given in the paper
    PROVED = {CYCLIC, DIVERGENT, TERMINAL}


class Family:
    """Which solved (or unsolved) family a universe belongs to.

    The names in parentheses are carykh's informal names from
    "The Collatz Multiverse"; they are kept because they are memorable and
    because the paper cites them.
    """
    CONSTANT = "constant"                # a = 0                (hub-and-spoke)
    PURE_SHAPE = "pure-cycle"            # b = 0, a = 2^t       (shapes)
    PURE_RUNAWAY = "pure-runaway"        # b = 0, a not 2^t     (shape-row runaways)
    PARITY_RUNAWAY = "parity-runaway"    # a + b odd            (dumbass / runaway)
    HALVING = "halving-reducible"        # a, b both even       (even parallel)
    ATTRACTING = "attracting-reducible"  # odd p | gcd(a,b)     (odd parallel, connected)
    DESCENT = "descent"                  # a = 1, b odd         (black hole)
    PRIMITIVE = "primitive"              # a >= 3 odd, b odd, gcd = 1


class Knowledge:
    """How much is known about a universe -- a coarser, honest grading than
    `Family`, and the one that matters when deciding what is worth studying.

    The four tiers are ordered by decreasing knowledge.  The distinction
    between CLOSED and DECIDED is whether the *cycle structure* is given by a
    formula or merely by a terminating computation; the distinction between
    REDUCIBLE and OPEN is whether the universe is its own normal form.
    """

    #: fate proved AND the complete cycle set given in closed form.
    #: a = 0, b = 0, and the parity runaways.
    CLOSED = "closed form"

    #: fate proved, cycle set finite and computable for each b, but with no
    #: known formula in b.  This is exactly the a = 1 row: Theorem "descent"
    #: bounds every cycle's least element by b, so testing 1..b decides it,
    #: yet the counts (1, 2, 2, 3, 3, 2, 2, 5, 3, 2, 6, ...) follow no known
    #: pattern.
    DECIDED = "fate proved, cycles computable"

    #: fate unknown, but the universe reduces to a strictly smaller open one,
    #: so it contains no mathematics the smaller one does not already have.
    REDUCIBLE = "reduces to a smaller open universe"

    #: fate unknown and irreducible -- its own normal form.  These are the
    #: only universes where new work is possible.
    OPEN = "open and minimal"

    ORDER = [CLOSED, DECIDED, REDUCIBLE, OPEN]


def knowledge(a: int, b: int) -> str:
    """Which `Knowledge` tier the universe T_{a,b} occupies."""
    u = classify(a, b)
    na, nb = u.normal
    nu = classify(na, nb if b >= 0 else -nb)
    if nu.fate == Fate.OPEN:
        return (Knowledge.OPEN if (u.a, abs(u.b)) == u.normal
                else Knowledge.REDUCIBLE)
    if nu.family == Family.DESCENT:
        return Knowledge.DECIDED
    return Knowledge.CLOSED


@dataclass(frozen=True)
class Reduction:
    """One step of the reduction of a universe to its normal form."""
    kind: str          # "halving" or "attraction"
    src: Tuple[int, int]
    dst: Tuple[int, int]
    scale: int         # the d with dst embedded as d*Z, or 2 for halving
    note: str


@dataclass
class Universe:
    """A fully classified generalised Collatz map."""
    a: int
    b: int
    family: str
    fate: str
    conjecture: str                       # what is believed when fate is OPEN
    reason: str                           # one-line justification / proof pointer
    normal: Tuple[int, int]               # coprime normal form
    chain: List[Reduction] = field(default_factory=list)
    attracting: Dict[int, int] = field(default_factory=dict)   # p -> v_p(b)
    repelling: Dict[int, int] = field(default_factory=dict)    # p -> v_p(b)
    drift: float = 0.0                    # geometric drift per T-step
    odd_drift: float = 0.0                # expected ratio per odd->odd step

    # ---- convenience -------------------------------------------------

    @property
    def label(self) -> str:
        return f"{self.a}x{self.b:+d}"

    @property
    def is_proved(self) -> bool:
        return self.fate in Fate.PROVED

    @property
    def is_reducible(self) -> bool:
        return bool(self.chain)

    @property
    def is_primitive(self) -> bool:
        return self.family == Family.PRIMITIVE

    @property
    def knowledge(self) -> str:
        """The `Knowledge` tier -- see `knowledge`."""
        return knowledge(self.a, self.b)

    def __str__(self) -> str:
        nf = f"{self.normal[0]}x{self.normal[1]:+d}"
        tail = "" if (self.a, self.b) == self.normal else f"  ->  {nf}"
        return f"{self.label}: {self.family}, {self.fate}{tail}"


def drift(a: int) -> Tuple[float, float]:
    """The two standard heuristic drift constants of the a-row.

    Returns (per_step, per_odd_step):

      * per_step   = sqrt(a)/2 -- the geometric mean of the two branch
        multipliers a and 1/2 taken with equal weight; this is carykh's
        "gravity".
      * per_odd_step = a/4 -- the expected ratio between consecutive *odd*
        terms, using E[v_2(an+b)] = 2 for the accelerated map.

    Both cross 1 at a = 4, so a in {1, 3} contracts and a >= 5 expands.
    """
    return (math.sqrt(a) / 2.0 if a > 0 else 0.0, a / 4.0)


def attracting_primes(a: int, b: int) -> Dict[int, int]:
    """Odd primes p with p | a and p | b.  For each, p^{v_p(b)} Z is an
    attracting invariant sub-universe (Theorem: p-adic stratification, (i))."""
    if b == 0:
        return {}
    out = {}
    for p in factorise(abs(a)):
        if p == 2:
            continue
        e = vp(b, p) if b % p == 0 else 0
        if e:
            out[p] = e
    return out


def repelling_primes(a: int, b: int) -> Dict[int, int]:
    """Odd primes p with p | b and p does not divide a.  For each,
    min(v_p(n), v_p(b)) is an invariant of the dynamics, splitting the state
    space into v_p(b) + 1 mutually unreachable strata (stratification, (ii))."""
    if b == 0:
        return {}
    out = {}
    for p, e in factorise(abs(b)).items():
        if p == 2:
            continue
        if a % p != 0:
            out[p] = e
    return out


def sub_universes(a: int, b: int) -> Dict[int, Tuple[int, int]]:
    """The scaled copies embedded in T_{a,b}: for each odd divisor d of b,
    the set d*Z is invariant and T_{a,b} restricted to it is conjugate, via
    n -> n/d, to T_{a, b/d}."""
    if b == 0:
        return {}
    return {d: (a, b // d) for d in odd_divisors(b)}


def reduction_chain(a: int, b: int) -> Tuple[Tuple[int, int], List[Reduction]]:
    """Reduce (a, b) to its normal form, recording every step.

    Two rewrite rules, applied until neither fires:

      (H) halving      -- if 2 | a and 2 | b then (a, b) -> (a/2, b/2).
      (A) attraction   -- if p is an odd prime dividing both a and b, then
                          every orbit is absorbed into p^{v_p(b)} Z, on which
                          the map is conjugate to (a, b / p^{v_p(b)}).

    The rules commute, so the normal form is unique; it always satisfies
    gcd(a', b') = 1 -- but only for a >= 1.  At a = 0 every prime divides a,
    rule (A) would be applicable for every odd prime at once, and gcd(0,b)=b,
    so the coprimality claim genuinely fails there; we simply do not apply
    (A) when a = 0, because `classify` settles that row outright as the
    constant family and never consults the normal form.  See the paper,
    Theorem "normal form" and the remark following it.
    """
    chain: List[Reduction] = []
    cur = (a, b)
    guard = 0
    while True:
        guard += 1
        if guard > 256:                                   # cannot happen
            raise RuntimeError("reduction failed to terminate")
        ca, cb = cur
        # (H) halving
        if ca % 2 == 0 and cb % 2 == 0 and not (ca == 0 and cb == 0):
            nxt = (ca // 2, cb // 2)
            chain.append(Reduction(
                "halving", cur, nxt, 2,
                f"{ca}x{cb:+d} inserts one extra even term after each odd "
                f"step of {nxt[0]}x{nxt[1]:+d}"))
            cur = nxt
            continue
        # (A) attraction
        if cb != 0:
            att = attracting_primes(ca, cb)
            if att:
                p = min(att)
                e = att[p]
                d = p ** e
                nxt = (ca, cb // d)
                chain.append(Reduction(
                    "attraction", cur, nxt, d,
                    f"every orbit enters {d}Z after at most {e} odd "
                    f"step{'' if e == 1 else 's'}; "
                    f"on {d}Z the map is n -> {d}*({nxt[0]}x{nxt[1]:+d})(n/{d})"))
                cur = nxt
                continue
        break
    return cur, chain


def normal_form(a: int, b: int) -> Tuple[int, int]:
    """The coprime normal form of (a, b)."""
    return reduction_chain(a, b)[0]


def classify(a: int, b: int) -> Universe:
    """Full classification of the universe T_{a,b} over the positive integers.

    Only a, b >= 0 are classified as such; for b < 0 the negation duality
    n -> -n conjugates T_{a,b} on the negatives to T_{a,-b} on the positives,
    and we classify |b| and flag it.
    """
    if a < 0:
        raise ValueError("negative multipliers are not part of this family")

    negated = b < 0
    ab, bb = a, abs(b)

    norm, chain = reduction_chain(ab, bb)
    att = attracting_primes(ab, bb)
    rep = repelling_primes(ab, bb)
    d_step, d_odd = drift(ab)

    def mk(family: str, fate: str, reason: str, conjecture: str = "") -> Universe:
        if negated:
            reason += ("  [stated for |b|; T_{%d,%d} on the negative integers "
                       "is conjugate to T_{%d,%d} on the positives via n -> -n]"
                       % (a, b, a, bb))
        return Universe(a=a, b=b, family=family, fate=fate,
                        conjecture=conjecture, reason=reason,
                        normal=norm, chain=chain,
                        attracting=att, repelling=rep,
                        drift=d_step, odd_drift=d_odd)

    # -- a = 0: every odd number is sent to the constant b ---------------
    if ab == 0:
        if bb == 0:
            return mk(Family.CONSTANT, Fate.TERMINAL,
                      "every orbit reaches the fixed point 0")
        L = v2(bb) + 1
        return mk(Family.CONSTANT, Fate.CYCLIC,
                  f"single cycle {bb} -> ... -> oddpart({bb})={odd_part(bb)} -> {bb} "
                  f"of length {L}; every orbit enters it")

    # -- b = 0: odd numbers are multiplied, evens halved ------------------
    if bb == 0:
        u = odd_part(ab)
        if u == 1:
            t = v2(ab) if ab % 2 == 0 else 0
            return mk(Family.PURE_SHAPE, Fate.CYCLIC,
                      f"a = 2^{t}; every odd n lies on the cycle "
                      f"n -> 2^{t}n -> ... -> n of length {t + 1}")
        return mk(Family.PURE_RUNAWAY, Fate.DIVERGENT,
                  f"odd part of a is {u} >= 3; on odd numbers the map acts as "
                  f"n -> {u}n, which is strictly increasing")

    # -- opposite parities: odd numbers never map to even numbers ---------
    if (ab + bb) % 2 == 1:
        kind = "linearly" if ab == 1 else "exponentially"
        return mk(Family.PARITY_RUNAWAY, Fate.DIVERGENT,
                  f"a + b is odd, so a*n + b is odd for odd n; the orbit is "
                  f"eventually a strictly increasing sequence of odd numbers "
                  f"growing {kind}")

    # -- both even: halving symmetry --------------------------------------
    if ab % 2 == 0 and bb % 2 == 0:
        base = classify(norm[0], norm[1] if not negated else -norm[1])
        return mk(Family.HALVING, base.fate,
                  f"halving symmetry: reduces to {norm[0]}x{norm[1]:+d} "
                  f"({base.fate})", base.conjecture)

    # -- both odd ---------------------------------------------------------
    if ab == 1:
        return mk(Family.DESCENT, Fate.CYCLIC,
                  f"a = 1 with b odd: for odd n > b, T^2(n) = (n+b)/2 < n, and "
                  f"T(n) < n for even n, so every orbit descends into [1, {bb}] "
                  f"and must cycle")

    if att:
        base = classify(norm[0], norm[1] if not negated else -norm[1])
        ps = ", ".join(f"{p}^{e}" for p, e in sorted(att.items()))
        return mk(Family.ATTRACTING, base.fate,
                  f"attracting primes {ps} divide gcd(a,b); every orbit is "
                  f"absorbed into the scaled copy of {norm[0]}x{norm[1]:+d}",
                  base.conjecture)

    # primitive: a >= 3 odd, b odd, gcd(a, b) = 1
    if ab == 3:
        conj = ("conjecturally every orbit is eventually periodic "
                "(drift 3/4 < 1 per odd step)")
    else:
        conj = (f"conjecturally almost every orbit diverges "
                f"(drift {ab}/4 > 1 per odd step); finitely many cycles are "
                f"still expected")
    return mk(Family.PRIMITIVE, Fate.OPEN,
              "a >= 3 odd, b odd, gcd(a, b) = 1: no reduction applies and no "
              "proof is known", conj)


def radical(n: int) -> int:
    """Product of the distinct primes of n != 0 (rad(1) = 1)."""
    r = 1
    for p in factorise(abs(n)):
        r *= p
    return r


def reduces_to_offset_one(a: int, b: int) -> bool:
    """True iff T_{a,b} is, on a global attractor, a scaled copy of T_{a,1}.

    The criterion is rad(b) | a -- weaker than the one-step condition b | a,
    which misses 3x+9, 3x+27, 5x+25 and friends.  (Radical criterion.)
    """
    if b == 0:
        return False
    return all(a % p == 0 for p in factorise(abs(b)))


def one_is_periodic(a: int, b: int, max_steps: int = 5000,
                    value_cap: int = 10 ** 60) -> Tuple[bool, Optional[int]]:
    """Is 1 on a cycle of T_{a,b}?

    Returns (periodic, index) where `index` is the first step at which the
    orbit of 1 meets a power of two -- the two are equivalent for a, b >= 1
    (power-of-two criterion).
    """
    n = 1
    for i in range(max_steps):
        if i and n > 0 and (n & (n - 1)) == 0:
            return True, i
        if abs(n) > value_cap:
            return False, None
        n = step(n, a, b)
        if n == 0:
            return False, None
    return False, None


def half_line_invariance(a: int, b: int) -> Tuple[bool, bool]:
    """(is Z_{>=1} invariant, is Z_{<=-1} invariant) under T_{a,b}.

    Z_{>=1} is invariant iff a + b >= 1;  Z_{<=-1} iff b <= a - 1.
    Outside those ranges only finitely many integers cross: the sign can
    change only at an odd n with |n| <= |b|/a.
    """
    return (a + b >= 1, b <= a - 1)


# ======================================================================
# 4.  Cycles
# ======================================================================

@dataclass(frozen=True)
class Cycle:
    """A periodic orbit of T_{a,b}, normalised to start at its least element."""
    a: int
    b: int
    elements: Tuple[int, ...]

    @property
    def length(self) -> int:
        return len(self.elements)

    @property
    def k(self) -> int:
        """Number of odd terms = number of `a n + b` steps per period."""
        return sum(1 for x in self.elements if x % 2 == 1)

    @property
    def m(self) -> int:
        """Number of halvings per period."""
        return self.length - self.k

    @property
    def minimum(self) -> int:
        return min(self.elements)

    @property
    def maximum(self) -> int:
        return max(self.elements)

    @property
    def divisor(self) -> int:
        """The odd divisor d of b such that this cycle is d times a
        *primitive* cycle of T_{a, b/d}.  See `decompose_cycles`."""
        if self.b == 0:
            return 1
        d = 1
        for p, e in repelling_primes(self.a, self.b).items():
            k = min(min(vp(x, p) if x % p == 0 else 0 for x in self.elements), e)
            d *= p ** k
        return d

    @property
    def is_primitive(self) -> bool:
        return self.divisor == 1

    def __str__(self) -> str:
        return (f"[{self.length}] " + " -> ".join(map(str, self.elements))
                + f" -> {self.elements[0]}")


def _normalise_cycle(seq: Sequence[int]) -> Tuple[int, ...]:
    m = min(seq)
    i = list(seq).index(m)
    return tuple(seq[i:]) + tuple(seq[:i])


def find_cycles(a: int, b: int, seed_max: int = 2_000,
                max_steps: int = 20_000,
                value_cap: Optional[int] = None,
                seeds: Optional[Iterable[int]] = None) -> List[Cycle]:
    """Census of the cycles reachable from small seeds.

    This is a *search*, not a proof: it finds every cycle that some seed
    n <= seed_max falls into within the step and value budget.  Cycles whose
    basin misses that window are missed, so the counts below are lower
    bounds.  (Artem makes the same caveat about his loop counts.)
    """
    if value_cap is None:
        value_cap = max(10 ** 18, (seed_max + abs(b)) * max(a, 1) ** 12)

    found: Dict[Tuple[int, ...], Cycle] = {}
    # memo: n -> True if n is known to reach an already-recorded cycle,
    #       False if n is known to escape the budget
    settled: Dict[int, bool] = {}

    src = range(1, seed_max + 1) if seeds is None else seeds
    for s in src:
        n = s
        seen: Dict[int, int] = {}
        traj: List[int] = []
        escaped = False
        for _ in range(max_steps):
            if n in settled:
                escaped = not settled[n]
                break
            if n in seen:
                cyc = _normalise_cycle(traj[seen[n]:])
                if cyc not in found:
                    found[cyc] = Cycle(a, b, cyc)
                break
            if abs(n) > value_cap:
                escaped = True
                break
            seen[n] = len(traj)
            traj.append(n)
            n = step(n, a, b)
        else:
            escaped = True
        for x in traj:
            settled[x] = not escaped

    return sorted(found.values(), key=lambda c: (c.minimum, c.length))


def cycle_equation_residual(c: Cycle) -> int:
    """Check the cycle equation

        n1 * (2^m - a^k) = b * sum_{i=1..k} a^(k-i) * 2^(d_1 + ... + d_{i-1})

    where n1 is the least *odd* element, k the number of odd steps, m the
    number of halvings, and d_i the run of halvings after the i-th odd step.
    Returns lhs - rhs, which must be 0.
    """
    a, b = c.a, c.b
    els = list(c.elements)
    # rotate so that the cycle starts at its least odd element
    odds = [i for i, x in enumerate(els) if x % 2 == 1]
    if not odds:
        return 0
    start = min(odds, key=lambda i: els[i])
    els = els[start:] + els[:start]

    n1 = els[0]
    ds: List[int] = []
    run = 0
    for x in els[1:] + [els[0]]:
        if x % 2 == 0:
            run += 1
        else:
            ds.append(run if run else 0)
            run = 0
    if run:
        ds.append(run)
    # ds[i] is the number of halvings after the (i+1)-th odd step
    k = c.k
    m = c.m
    lhs = n1 * (2 ** m - a ** k)
    rhs = 0
    prefix = 0
    for i in range(k):
        rhs += b * (a ** (k - 1 - i)) * (2 ** prefix)
        prefix += ds[i] if i < len(ds) else 0
    return lhs - rhs


def decompose_cycles(a: int, b: int, cycles: Sequence[Cycle]
                     ) -> Dict[int, List[Cycle]]:
    """Group cycles by the divisor d of b that they carry.

    The divisor decomposition theorem says

        Cyc(T_{a,b})  =  disjoint union over odd d | b  of
                         d * PrimCyc(T_{a, b/d}),

    so grouping by `Cycle.divisor` and dividing through by d must recover
    exactly the primitive cycles of the smaller universe.
    """
    out: Dict[int, List[Cycle]] = {}
    for c in cycles:
        out.setdefault(c.divisor, []).append(c)
    return dict(sorted(out.items()))


# ======================================================================
# 5.  Bulk statistics (carykh's heat maps)
# ======================================================================

def growth_statistics(a: int, b: int, n_max: int = 10_000,
                      max_steps: int = 5_000,
                      value_cap: int = 10 ** 30) -> Dict[str, object]:
    """Average relative peak and average path length over seeds 1..n_max.

    * "relative peak" of n is max(orbit(n)) / n, and we report the geometric
      mean over all seeds -- carykh's "average max growth".
    * "path length" is the number of steps until the first repeat, and we
      report the arithmetic mean.

    Seeds whose orbit blows past `value_cap` or `max_steps` are counted as
    runaways and excluded from the means; the runaway fraction is reported.
    """
    log_sum = 0.0
    len_sum = 0
    counted = 0
    runaway = 0

    for s in range(1, n_max + 1):
        n = s
        peak = s
        seen: Dict[int, int] = {}
        steps = 0
        blew = False
        while steps < max_steps:
            if n in seen:
                break
            if abs(n) > value_cap:
                blew = True
                break
            seen[n] = steps
            if abs(n) > peak:
                peak = abs(n)
            n = step(n, a, b)
            steps += 1
        else:
            blew = True
        if blew:
            runaway += 1
            continue
        counted += 1
        len_sum += steps
        log_sum += math.log(peak / s)

    if counted == 0:
        return {"a": a, "b": b, "peak": None, "path": None,
                "runaway_fraction": 1.0, "counted": 0}
    return {
        "a": a, "b": b,
        "peak": math.exp(log_sum / counted),
        "path": len_sum / counted,
        "runaway_fraction": runaway / n_max,
        "counted": counted,
    }


# ======================================================================
# 6.  Grid rendering
# ======================================================================

#: compact codes used in the printed universe tables
CODE = {
    Family.CONSTANT: "C",
    Family.PURE_SHAPE: "S",
    Family.PURE_RUNAWAY: "R",
    Family.PARITY_RUNAWAY: "R",
    Family.HALVING: "H",
    Family.ATTRACTING: "A",
    Family.DESCENT: "D",
    Family.PRIMITIVE: "?",
}

CODE_LEGEND = [
    ("C", Family.CONSTANT, "a = 0: one cycle, every orbit enters it"),
    ("S", Family.PURE_SHAPE, "b = 0, a a power of 2: every odd n is on a cycle"),
    ("R", "runaway", "all orbits diverge (b = 0 with odd part > 1, or a + b odd)"),
    ("H", Family.HALVING, "a, b both even: halving symmetry"),
    ("A", Family.ATTRACTING, "odd prime divides gcd(a, b): absorbed into a scaled copy"),
    ("D", Family.DESCENT, "a = 1, b odd: two-step descent forces a cycle"),
    ("?", Family.PRIMITIVE, "irreducible and open"),
]


def grid(a_max: int, b_max: int, a_min: int = 0, b_min: int = 0
         ) -> List[List[Universe]]:
    """Row-major grid of classified universes, rows indexed by a."""
    return [[classify(a, b) for b in range(b_min, b_max + 1)]
            for a in range(a_min, a_max + 1)]


def render_grid(a_max: int, b_max: int, a_min: int = 0, b_min: int = 0) -> str:
    """ASCII rendering of the classification grid (the 'table of universes')."""
    rows = grid(a_max, b_max, a_min, b_min)
    w = max(2, len(str(b_max)) + 1)
    head = "  a\\b " + "".join(f"{b:>{w}}" for b in range(b_min, b_max + 1))
    out = [head, "      " + "-" * (w * (b_max - b_min + 1))]
    for a, row in zip(range(a_min, a_max + 1), rows):
        out.append(f"{a:>5} " + "".join(f"{CODE[u.family]:>{w}}" for u in row))
    out.append("")
    out.append("legend:")
    for code, _, desc in CODE_LEGEND:
        out.append(f"  {code}  {desc}")
    return "\n".join(out)


# ======================================================================
# 7.  CLI
# ======================================================================

def _report(a: int, b: int, seed_max: int = 1000) -> str:
    u = classify(a, b)
    lines = [f"=== {u.label} " + "=" * (60 - len(u.label)),
             f"family      : {u.family}",
             f"fate        : {u.fate}" + ("  (PROVED)" if u.is_proved else "")]
    if u.conjecture:
        lines.append(f"conjecture  : {u.conjecture}")
    lines.append(f"reason      : {u.reason}")
    lines.append(f"drift       : {u.drift:.4f} per step, {u.odd_drift:.4f} per odd step")
    lines.append(f"normal form : {u.normal[0]}x{u.normal[1]:+d}")
    if u.chain:
        for r in u.chain:
            lines.append(f"   {r.kind:<11} {r.src[0]}x{r.src[1]:+d} -> "
                         f"{r.dst[0]}x{r.dst[1]:+d}   ({r.note})")
    if u.attracting:
        lines.append(f"attracting  : " + ", ".join(f"{p}^{e}" for p, e in sorted(u.attracting.items())))
    if u.repelling:
        lines.append(f"repelling   : " + ", ".join(f"{p}^{e}" for p, e in sorted(u.repelling.items()))
                     + "   (state space splits into mutually unreachable strata)")
    if b > 0:
        subs = sub_universes(a, b)
        if len(subs) > 1:
            lines.append("sub-copies  : " + ", ".join(
                f"{d}*({sa}x{sb:+d})" for d, (sa, sb) in subs.items() if d > 1))

    cycles = find_cycles(a, b, seed_max=seed_max)
    lines.append(f"cycles found (seeds 1..{seed_max}): {len(cycles)}")
    groups = decompose_cycles(a, b, cycles)
    for d, cs in groups.items():
        tag = "primitive" if d == 1 else f"= {d} * primitive cycles of {a}x{b // d:+d}"
        lines.append(f"  divisor {d:<6} ({len(cs)}) {tag}")
        for c in cs:
            res = cycle_equation_residual(c)
            ok = "ok" if res == 0 else f"RESIDUAL {res}"
            head = list(c.elements[:12])
            more = "" if c.length <= 12 else f" ... (+{c.length - 12})"
            lines.append(f"     len {c.length:<4} k={c.k:<3} m={c.m:<3} min={c.minimum:<8} "
                         f"max={c.maximum:<12} [{ok}]")
            lines.append(f"       {head}{more}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = p.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("report", help="full report on one universe")
    q.add_argument("a", type=int)
    q.add_argument("b", type=int)
    q.add_argument("--seeds", type=int, default=1000)

    g = sub.add_parser("grid", help="classification grid")
    g.add_argument("--amax", type=int, default=12)
    g.add_argument("--bmax", type=int, default=12)

    s = sub.add_parser("stats", help="growth statistics for one universe")
    s.add_argument("a", type=int)
    s.add_argument("b", type=int)
    s.add_argument("--nmax", type=int, default=10000)

    args = p.parse_args(argv)
    if args.cmd == "report":
        print(_report(args.a, args.b, args.seeds))
    elif args.cmd == "grid":
        print(render_grid(args.amax, args.bmax))
    elif args.cmd == "stats":
        st = growth_statistics(args.a, args.b, n_max=args.nmax)
        print(st)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
