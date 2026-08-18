"""
qary.py -- the q-ary Collatz-type maps, and predicate-driven iterations.

Two generalisations of  T_{a,b}(n) = n/2 (even), a n + b (odd), corresponding
to Chapters "The q-ary multiverse" and "Beyond modularity" of the paper
../paper/collatz_multiverse.tex.

  1. THE q-ARY MAP.  Fix q >= 2 and coefficients a_i, b_i for i = 1..q-1:

         F(n) = a_i n + b_i    if n = i (mod q),  1 <= i <= q-1
                n / q          if n = 0 (mod q).

     q = 2 is the two-parameter family of the rest of the paper.

  2. PREDICATE MAPS.  Drop modularity entirely: choose the branch by any
     predicate on n (primality, squarefreeness, digit sums, ...).  Almost
     nothing survives, and this module is mostly here to show what breaks
     and to run the experiments quoted in the paper.

Everything is exact integer arithmetic.

Author: RobinCodes.  Written with AI assistance; see the paper's note on the
use of artificial intelligence.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "QMap",
    "residue_graph",
    "escaping_residues",
    "qary_drift",
    "qary_drift_threshold",
    "PredicateMap",
    "is_prime",
    "primality_map",
]


# ======================================================================
# 1.  The q-ary map
# ======================================================================

class QMap:
    """F(n) = a_i n + b_i for n = i (mod q), i != 0;  n/q for n = 0 (mod q)."""

    def __init__(self, q: int, a: Sequence[int], b: Sequence[int]):
        if q < 2:
            raise ValueError("q >= 2 (q = 1 makes F the identity)")
        if len(a) != q - 1 or len(b) != q - 1:
            raise ValueError(f"need q-1 = {q - 1} coefficients, got "
                             f"{len(a)} and {len(b)}")
        self.q = q
        self.a = list(a)          # a[i-1] is the multiplier for residue i
        self.b = list(b)

    # ---- dynamics ----------------------------------------------------

    def step(self, n: int) -> int:
        i = n % self.q
        if i == 0:
            return n // self.q
        return self.a[i - 1] * n + self.b[i - 1]

    def orbit(self, n: int, max_steps: int = 10_000,
              value_cap: Optional[int] = None
              ) -> Tuple[List[int], Optional[int]]:
        seen: Dict[int, int] = {}
        traj: List[int] = []
        for k in range(max_steps):
            if n in seen:
                return traj, seen[n]
            if value_cap is not None and abs(n) > value_cap:
                return traj, None
            seen[n] = k
            traj.append(n)
            n = self.step(n)
        return traj, None

    # ---- the two symmetries ------------------------------------------

    def scaled(self, c: int) -> "QMap":
        """The map with all coefficients multiplied by c.

        For c = q this is the q-ary halving symmetry: F_{q a, q b} refines
        F_{a,b}, inserting one extra division after each affine step.
        """
        return QMap(self.q, [c * x for x in self.a], [c * x for x in self.b])

    def offset_scaled(self, d: int) -> "QMap":
        """The image of this map under n -> d n, for d coprime to q.

        n = i (mod q) becomes d n = d i (mod q), so the branches are permuted
        by multiplication by d; the multipliers travel with them and the
        offsets pick up a factor d.  This is the q-ary form of the odd
        scaling symmetry.
        """
        q = self.q
        if math.gcd(d, q) != 1:
            raise ValueError("scaling factor must be coprime to q")
        a2 = [0] * (q - 1)
        b2 = [0] * (q - 1)
        for i in range(1, q):
            j = (d * i) % q
            if j == 0:
                raise ValueError("d must be invertible mod q")
            a2[j - 1] = self.a[i - 1]
            b2[j - 1] = d * self.b[i - 1]
        return QMap(q, a2, b2)

    def __repr__(self) -> str:
        parts = [f"{self.a[i-1]}n{self.b[i-1]:+d} if n={i}" for i in range(1, self.q)]
        return f"QMap(q={self.q}: " + ", ".join(parts) + f", n/{self.q} if n=0)"


# ======================================================================
# 2.  The residue obstruction -- the q-ary parity obstruction
# ======================================================================

def residue_graph(m: QMap) -> Dict[int, int]:
    """i -> (a_i i + b_i) mod q, for i != 0.

    For a non-dividing branch the next residue is determined by the current
    one, because n = i (mod q) gives a_i n + b_i = a_i i + b_i (mod q).  The
    dividing branch is NOT determined mod q -- n/q depends on n mod q^2 --
    which is why the obstruction only sees the affine part.
    """
    return {i: (m.a[i - 1] * i + m.b[i - 1]) % m.q for i in range(1, m.q)}


def escaping_residues(m: QMap) -> List[int]:
    """Residues from which the affine part alone never reaches 0 mod q.

    Every orbit entering such a residue class never again meets the dividing
    branch, so with positive multipliers it grows without bound.  For q = 2
    this is exactly "a + b odd".
    """
    g = residue_graph(m)
    out = []
    for start in range(1, m.q):
        seen = set()
        i = start
        while i != 0 and i not in seen:
            seen.add(i)
            i = g[i]
        if i != 0:
            out.append(start)
    return out


def qary_drift(m: QMap) -> float:
    """Heuristic geometric drift per affine step.

    An affine step multiplies by roughly a_i; if its image is divisible by q
    then the expected number of consecutive divisions is q/(q-1).  Averaging
    the multipliers geometrically gives

        delta = (prod_i a_i)^(1/(q-1)) / q^(q/(q-1)),

    so the map is heuristically contracting iff prod_i a_i < q^q.
    For q = 2 this reads a/4, the classical threshold a < 4.
    """
    prod = 1
    for x in m.a:
        prod *= abs(x)
    if prod == 0:
        return 0.0
    k = m.q - 1
    return prod ** (1.0 / k) / m.q ** (m.q / k)


def qary_drift_threshold(q: int) -> int:
    """prod_i a_i must be below q^q for heuristic contraction."""
    return q ** q


# ======================================================================
# 3.  Beyond modularity: predicate-driven iteration
# ======================================================================

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    r = int(math.isqrt(n))
    f = 3
    while f <= r:
        if n % f == 0:
            return False
        f += 2
    return True


class PredicateMap:
    """n -> f_j(n) where j is the first predicate satisfied by n.

    `branches` is a list of (name, predicate, function) tried in order; the
    last entry should be a catch-all.
    """

    def __init__(self, branches: Sequence[Tuple[str, Callable[[int], bool],
                                                Callable[[int], int]]]):
        self.branches = list(branches)

    def branch_of(self, n: int) -> str:
        for name, pred, _ in self.branches:
            if pred(n):
                return name
        raise ValueError(f"no branch applies to {n}")

    def step(self, n: int) -> int:
        for _, pred, fn in self.branches:
            if pred(n):
                return fn(n)
        raise ValueError(f"no branch applies to {n}")

    def orbit(self, n: int, max_steps: int = 10_000,
              value_cap: Optional[int] = None
              ) -> Tuple[List[int], Optional[int]]:
        seen: Dict[int, int] = {}
        traj: List[int] = []
        for k in range(max_steps):
            if n in seen:
                return traj, seen[n]
            if value_cap is not None and abs(n) > value_cap:
                return traj, None
            seen[n] = k
            traj.append(n)
            n = self.step(n)
        return traj, None


def primality_map() -> PredicateMap:
    """f(n) = 3n+1 if n is prime, n/2 if n is even, n+1 otherwise.

    The map from the research notes.  Its branch predicate is primality, which
    is not a congruence condition, so none of the reduction theory applies.
    What does apply is the density heuristic: the primes have density 0, so
    the growing branch is asymptotically negligible and the map behaves like
    n -> n/2 (even), n+1 (odd), which is T_{1,1} and provably collapses.
    """
    return PredicateMap([
        ("prime", is_prime, lambda n: 3 * n + 1),
        ("even", lambda n: n % 2 == 0, lambda n: n // 2),
        ("other", lambda n: True, lambda n: n + 1),
    ])
