# Collatz

A repository containing tools for the Collatz conjecture, including sieving tools, a GUI-based application for analysis of generalized Collatz maps, a fast Collatz simulator, and many small, generic scripts including ones for backwards trees and for graphs.

## Contents

| Folder | What's in it |
| --- | --- |
| `General Collatz/Multiverse/` | Structure theory of `n -> n/2` (even), `n -> an+b` (odd): classification, symmetries, reductions, cycle census. Plus `qary.py` (the mod-`q` maps and predicate maps) and `literature.py` (the ccchallenge.org corpus, classified). |
| `General Collatz/paper/` | **The Generalised Collatz Multiverse** — symmetries, reductions and fates of the `(a, b)` family, stated over ℤ. Single self-contained `.tex`. |
| `General Collatz/Collatz Program/` | Tk + matplotlib orbital analyser, with the interactive **Multiverse** workspace. |
| `General Collatz/General Map Enumerator/` | Bulk cycle data for `ax + b`, `a` odd up to 127, `b` odd up to 201. |
| `Sieve (Residual Analysis)/` | Terras-style residue sieve, with a machine-checked Rocq correctness proof and its paper. |
| `Fast Collatz/`, `Collatz Backwards/`, `Constellations/`, `Small Scripts/` | Simulators, inverse-tree tools, and assorted experiments. |

## The generalised multiverse

For integers `a, b >= 0` let

```
T(n) = n / 2      if n is even
       a*n + b    if n is odd
```

so that `T` with `(a, b) = (3, 1)` is the Collatz map. The paper in
`General Collatz/paper/` gives a complete structure theory of this family:

* **Two symmetries.** `(2a, 2b)` is a time-change of `(a, b)`, and for odd `d`
  the map `n -> dn` embeds `(a, b)` into `(a, db)`. These are the *only* affine
  equivalences — so the multiplier `a` is an invariant and no change of
  variable relates `3x+1` to `5x+1`.
* **One dichotomy.** For an odd prime `p`, whether `p` divides `a` decides
  everything: if it does, `p^v_p(b) Z` is a global attractor; if it does not,
  `min(v_p(n), v_p(b))` is conserved and the state space splits into
  mutually unreachable strata.
* **A normal form.** Those two rules are terminating and confluent, and the
  normal form is always coprime.
* **A complete classification.** After reduction every universe is one of
  `a' = 0`, `b' = 0`, `a' + b'` odd, `a' = 1` — all solved here — or else
  `a' >= 3` odd with `b'` odd and coprime, which is open.
* **Densities.** Exactly `1/3` of universes are open; `2/pi^2` are open and
  irreducible.
* **Over ℤ.** The positive integers are invariant exactly when `a + b >= 1`,
  the negative ones exactly when `b <= a - 1`, and only finitely many integers
  can ever change sign. The negatives of `ax+b` are the positives of `ax-b`,
  so `3x-1` is the other half of the Collatz map.
* **The cycle through 1.** `1` is periodic exactly when its orbit meets a
  power of two; `a + b = 2^k` is the one-step case.

### Beyond mod 2

Two further chapters push outward:

* **The q-ary multiverse** (`f(n) = a_i n + b_i` for `n = i mod q`, `n/q`
  otherwise). Both symmetries survive verbatim; the parity obstruction becomes
  a **residue graph** `i -> a_i·i + b_i mod q`, and a residue whose forward
  orbit avoids `0` can never divide; the drift threshold `a < 4` becomes
  `prod a_i < q^q`. Rigidity *fails* for `q >= 3`, because scaling permutes
  the branches.
* **Beyond modularity** — branches chosen by any predicate, not a congruence.
  *Periodic* (congruence) predicates land inside the theory; whether anything
  else can is an open conjecture, not a theorem. For the
  primality map `3n+1` if prime, `n/2` if even, `n+1` otherwise, divergence
  would need **63.09%** (`ln2/ln3`) of the odd values visited to be prime;
  the measured figure falls to **8.4% at 10^11** — though still ~2.3× the
  random `1/ln n`, so the naive "primes have density 0" argument is too glib.
  All 200,000 seeds tested are eventually periodic, into exactly two cycles.

Three conjectures from the earlier research programme are refuted in the
paper, with counterexamples in `2x+1`, `5x+1` and `3x+7`, and the claim that a
`v2`-preserving `g` conjugates `T` to `T_g` is refuted by
`T(9,3)(3) = 30 != 12`.

Of the nine universes carykh singles out as unresolved, three are solved, two
reduce, and **four are genuinely open**: `3x+1`, `3x+5`, `5x+1`, `5x+3`.

### Running it

```bash
cd "General Collatz/Multiverse"

python3 multiverse.py report 3 15     # full report on one universe
python3 multiverse.py grid            # the classification grid
python3 generate_data.py              # regenerate every table in the paper
                                      #   + run the verification suite
python3 inline_tables.py              # splice those tables into the paper
python3 literature.py                 # classify the ccchallenge.org corpus
python3 literature.py --refresh       #   ... re-downloading it first
```

The paper is a **single self-contained `.tex`** with no `\input` of external
files, so it compiles on any online LaTeX renderer as a one-file upload.
`inline_tables.py` refreshes the tables in place between marker comments, so
nothing is hand-transcribed.

The interactive version is the **Multiverse** button in
`General Collatz/Collatz Program/Collatz_Program.py`: a clickable
classification grid, per-universe reports, a cycle census showing the divisor
decomposition, a side-by-side symmetry explorer, and heat maps.

The grid offers four views, because family alone is not enough to colour by —
`2x+2` and `6x+2` are both halving-reducible, but the first reduces to the
solved `1x+1` and the second to `3x+1`:

| View | Shows |
| --- | --- |
| `family + fate` | letter = family, colour = **proved fate** |
| `knowledge tier` | how much is known: `K` closed form, `D` fate proved but cycles only computable, `=` reducible to a smaller open universe, `?` open and minimal |
| `open & minimal only` | strikes out everything solved or reducible, leaving only the cells where new work is possible |
| `reduction target` | equivalence classes — cells sharing a colour are literally the same problem |

There are **seven panels**, one per chapter: Universe Map, Report, Cycle
Census, Symmetries, Heat Maps, **q-ary Maps** and **Beyond Modularity**. The
q-ary panel draws the residue graph `i -> a_i·i + b_i mod q` — escaping
residues in red, the dividing class in blue — so you can see at a glance
whether a map can ever divide. It also warns when the residue obstruction
overrides the drift: `q=3, a=(3,3), b=(1,1)` has drift `0.577` and *looks*
contracting, but both residues escape and 100% of orbits diverge.

The four tiers have densities `2/3`, `0`, `1/3 − 2/π²` and `2/π²`. The
`D` tier is exactly the `a = 1` row: its fate is proved in two lines, but its
cycle counts (`1, 2, 2, 3, 3, 2, 2, 5, 3, 2, 6, …`) follow no known pattern.

## Prior work

The multiverse framing and many of the phenomena the paper proves were found
experimentally by two YouTube mathematicians, and the paper attributes each
result explicitly:

* carykh, [*The Collatz Multiverse*](https://youtu.be/n63FBYqj98E), and the
  follow-up on his second channel lazykh,
  [*Collatz Multiverse Ramble, Part 2!*](https://youtu.be/3JO-8oZ-IlQ)
* Artem, [*The Collatz Multiverse Multiverse*](https://youtu.be/MNFWrB8iUbM)

## Note on the use of AI

Parts of this repository — the two papers, the Rocq development, the
`Multiverse` library and workspace, and the verification suites — were produced
in collaboration with an artificial-intelligence system, at the author's
direction. Each paper carries its own note saying exactly what was and was not
machine-assisted, and what is and is not machine-checked.

## License

MIT — see `LICENSE`.
