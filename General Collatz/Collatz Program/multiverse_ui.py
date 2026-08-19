"""
multiverse_ui.py -- the Multiverse workspace for Collatz_Program.py

Seven panels, one per chapter of the paper
"../paper/collatz_multiverse.tex":

    Universe Map        the classification grid, in four views: family+fate,
                        knowledge tier, open-and-minimal only, reduction target
    Report              family, fate, knowledge tier, the reduction chain, the
                        strata, behaviour over Z, and the cycle through 1
    Cycle Census        cycles with (k, m), the divisor decomposition, and a
                        live check of the cycle equation
    Symmetries          the halving and odd-scaling correspondences, shown
                        side by side on a chosen seed
    Heat Maps           relative peak / path length / cycle count / drift
    q-ary Maps          mod q instead of mod 2: the residue graph, escaping
                        residues, the two symmetries, the q^q drift threshold
    Beyond Modularity   branches chosen by a predicate rather than a
                        congruence -- the primality map and its density budget

The mathematics lives in ../Multiverse/multiverse.py and ../Multiverse/qary.py;
this file is only presentation.  It is imported lazily by Collatz_Program.py so
that the main program still runs if the engine is missing.

Author: RobinCodes.  Written with AI assistance; see the paper's note on the
use of artificial intelligence.
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Rectangle

# Deliberately NOT pyplot: pyplot keeps every figure it creates in a global
# registry, so an embedded figure made with plt.subplots() is never garbage
# collected and, under an interactive backend, can be shown in a window of
# its own.  Figure() + FigureCanvasTkAgg owns nothing globally.

# --- locate the engine -------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ENGINE = os.path.normpath(os.path.join(_HERE, "..", "Multiverse"))
if _ENGINE not in sys.path:
    sys.path.insert(0, _ENGINE)

import multiverse as mv  # noqa: E402
import qary as qa       # noqa: E402


# =====================================================================
#  Palette -- the same family colours the paper uses
# =====================================================================

FAMILY_COLOUR = {
    mv.Family.CONSTANT:       "#7fb3e8",
    mv.Family.PURE_SHAPE:     "#79c98a",
    mv.Family.PURE_RUNAWAY:   "#e0736f",
    mv.Family.PARITY_RUNAWAY: "#e0736f",
    mv.Family.HALVING:        "#b39ddb",
    mv.Family.ATTRACTING:     "#e8b465",
    mv.Family.DESCENT:        "#66c2c2",
    mv.Family.PRIMITIVE:      "#f2e14c",
}

FAMILY_BLURB = {
    mv.Family.CONSTANT:       "a = 0 -- one cycle, every orbit enters it",
    mv.Family.PURE_SHAPE:     "b = 0, a a power of 2 -- every odd n is on a cycle",
    mv.Family.PURE_RUNAWAY:   "b = 0, odd part of a > 1 -- all orbits diverge",
    mv.Family.PARITY_RUNAWAY: "a + b odd -- odd never maps to even, all diverge",
    mv.Family.HALVING:        "a, b both even -- halving symmetry",
    mv.Family.ATTRACTING:     "odd prime | gcd(a,b) -- absorbed into a scaled copy",
    mv.Family.DESCENT:        "a = 1, b odd -- two-step descent forces a cycle",
    mv.Family.PRIMITIVE:      "irreducible and OPEN",
}

# Family alone is NOT enough to colour by: 2x+2 and 6x+2 are both
# halving-reducible, but 2x+2 reduces to the solved 1x+1 while 6x+2 reduces to
# 3x+1 and is therefore exactly as open as Collatz.  Every view below encodes
# the fate or the knowledge tier, never the family on its own.

FATE_COLOUR = {
    mv.Fate.CYCLIC:    "#5fb36a",
    mv.Fate.DIVERGENT: "#d4645f",
    mv.Fate.TERMINAL:  "#7fb3e8",
    mv.Fate.OPEN:      "#f2e14c",
}

FATE_BLURB = {
    mv.Fate.CYCLIC:    "proved: every orbit is eventually periodic",
    mv.Fate.DIVERGENT: "proved: every orbit diverges",
    mv.Fate.TERMINAL:  "proved: every orbit reaches a fixed point",
    mv.Fate.OPEN:      "OPEN: no proof either way",
}

KNOWLEDGE_COLOUR = {
    mv.Knowledge.CLOSED:    "#3f8f57",
    mv.Knowledge.DECIDED:   "#4fb0c6",
    mv.Knowledge.REDUCIBLE: "#e0913f",
    mv.Knowledge.OPEN:      "#f2e14c",
}

KNOWLEDGE_CODE = {
    mv.Knowledge.CLOSED:    "K",
    mv.Knowledge.DECIDED:   "D",
    mv.Knowledge.REDUCIBLE: "=",
    mv.Knowledge.OPEN:      "?",
}

KNOWLEDGE_BLURB = {
    mv.Knowledge.CLOSED:
        "K  fully known -- fate proved AND every cycle in closed form",
    mv.Knowledge.DECIDED:
        "D  fate proved; cycles finite and computable, but no formula in b",
    mv.Knowledge.REDUCIBLE:
        "=  fate unknown, but equivalent to a strictly smaller open universe",
    mv.Knowledge.OPEN:
        "?  open AND minimal -- the only cells where new work is possible",
}

VIEWS = [
    "family + fate",
    "knowledge tier",
    "open & minimal only",
    "reduction target",
]


def _fmt_int(n: int, width: int = 18) -> str:
    """Readable form for a possibly astronomically large integer."""
    s = str(n)
    if len(s) <= width:
        return s
    return f"{s[:6]}...{s[-4:]} ({len(s)} digits)"


# =====================================================================
#  The window
# =====================================================================

class MultiverseWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.theme = getattr(parent, "theme", {
            "bg": "#050b1e", "panel": "#0b1633", "accent": "#143a8f",
            "text": "#c7d4ff", "highlight": "#2e7ddf"})

        self.title("Collatz Multiverse -- symmetries, reductions and fates")
        self.configure(bg=self.theme["bg"])

        # Fit the screen rather than assuming one: 1500x950 overflows a
        # 1366x768 laptop, which hides the status bar and the sash.
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(1500, sw - 80), min(950, sh - 120)
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2)}")
        self.minsize(980, 620)

        self._grid_cells = {}        # (a, b) -> Rectangle, for the map
        self._grid_range = (0, 12, 0, 12)
        self._selected = (3, 1)

        self.status = tk.StringVar(value="Ready")
        self._build()
        self.show_report(3, 1)

    # -----------------------------------------------------------------
    # chrome
    # -----------------------------------------------------------------

    def _build(self):
        self._configure_styles()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        self._build_map_tab()
        self._build_report_tab()
        self._build_cycles_tab()
        self._build_symmetry_tab()
        self._build_heat_tab()
        self._build_qary_tab()
        self._build_predicate_tab()

        bar = tk.Label(self, textvariable=self.status, bg=self.theme["panel"],
                       fg=self.theme["text"], anchor="w", padx=10)
        bar.pack(fill="x", side="bottom")

    def _frame(self, title):
        f = tk.Frame(self.nb, bg=self.theme["bg"])
        self.nb.add(f, text=title)
        return f

    def _label(self, parent, text, **kw):
        return tk.Label(parent, text=text, bg=self.theme["bg"],
                        fg=self.theme["text"], **kw)

    def _entry(self, parent, default, width=8):
        e = tk.Entry(parent, bg=self.theme["panel"], fg="white", width=width,
                     insertbackground="white", font=("Consolas", 10))
        e.insert(0, str(default))
        return e

    def _button(self, parent, text, cmd, accent=False):
        return tk.Button(parent, text=text, command=cmd,
                         bg=self.theme["highlight"] if accent else self.theme["accent"],
                         fg="white", font=("Arial", 9, "bold"))

    def _configure_styles(self):
        """Dark scrollbars.  The default ttk scrollbar is light grey and
        reads as a rendering artefact against the panel colour."""
        st = ttk.Style(self)
        for orient in ("Vertical", "Horizontal"):
            st.configure(
                f"MV.{orient}.TScrollbar",
                background=self.theme["accent"],
                troughcolor=self.theme["bg"],
                bordercolor=self.theme["bg"],
                arrowcolor=self.theme["text"],
                relief="flat")
            st.map(f"MV.{orient}.TScrollbar",
                   background=[("active", self.theme["highlight"])])

    def _scrolled_text(self, parent, wrap="none"):
        """A read-only text panel with BOTH scrollbars, on a grid.

        `tkinter.scrolledtext.ScrolledText` supplies a vertical bar only.
        Combined with wrap="none" that is a trap: a line wider than the panel
        is clipped at the bar with no way to scroll to the rest of it, so the
        text simply looks truncated -- and where the bar sits over the clip
        the two appear to overlap.  Gridding the text and both bars in their
        own cells fixes the reachability and the overlap at once.

        Returns the Text; its container is `.frame`, which is what the caller
        packs.
        """
        frame = tk.Frame(parent, bg=self.theme["panel"],
                         highlightthickness=1,
                         highlightbackground=self.theme["accent"])
        txt = tk.Text(frame, bg=self.theme["panel"], fg=self.theme["text"],
                      insertbackground="white", font=("Consolas", 10),
                      wrap=wrap, relief="flat", borderwidth=0,
                      padx=8, pady=6, highlightthickness=0)
        vsb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview,
                            style="MV.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=txt.xview,
                            style="MV.Horizontal.TScrollbar")
        txt.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # wheel scrolling, including shift+wheel for the horizontal axis
        txt.bind("<MouseWheel>",
                 lambda e: txt.yview_scroll(-1 * (e.delta // 120), "units"))
        txt.bind("<Shift-MouseWheel>",
                 lambda e: txt.xview_scroll(-1 * (e.delta // 120), "units"))
        txt.bind("<Button-4>", lambda e: txt.yview_scroll(-3, "units"))
        txt.bind("<Button-5>", lambda e: txt.yview_scroll(3, "units"))

        txt.frame = frame
        txt.config(state="disabled")
        return txt

    def _set_text(self, widget, content):
        """Replace a read-only panel's contents."""
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")
        widget.yview_moveto(0.0)
        widget.xview_moveto(0.0)

    def _copy(self, widget):
        self.clipboard_clear()
        self.clipboard_append(widget.get("1.0", "end-1c"))
        self._busy("panel contents copied to the clipboard")

    def _busy(self, msg):
        self.status.set(msg)
        self.update_idletasks()

    # =================================================================
    # Tab 1 -- Universe Map
    # =================================================================

    def _build_map_tab(self):
        f = self._frame("  Universe Map  ")

        ctl = tk.Frame(f, bg=self.theme["bg"])
        ctl.pack(fill="x", padx=10, pady=8)

        self._label(ctl, "a from").pack(side="left")
        self.map_a0 = self._entry(ctl, 0, 5); self.map_a0.pack(side="left", padx=3)
        self._label(ctl, "to").pack(side="left")
        self.map_a1 = self._entry(ctl, 12, 5); self.map_a1.pack(side="left", padx=3)
        self._label(ctl, "   b from").pack(side="left")
        self.map_b0 = self._entry(ctl, 0, 5); self.map_b0.pack(side="left", padx=3)
        self._label(ctl, "to").pack(side="left")
        self.map_b1 = self._entry(ctl, 12, 5); self.map_b1.pack(side="left", padx=3)
        self._button(ctl, "Draw", self.draw_map, accent=True).pack(side="left", padx=12)

        ctl2 = tk.Frame(f, bg=self.theme["bg"])
        ctl2.pack(fill="x", padx=10, pady=(0, 6))
        self._label(ctl2, "view").pack(side="left")
        self.map_view = ttk.Combobox(ctl2, width=24, state="readonly",
                                     values=VIEWS)
        self.map_view.current(0)
        self.map_view.pack(side="left", padx=6)
        self.map_view.bind("<<ComboboxSelected>>", lambda _e: self.draw_map())
        self._label(ctl2, "click a cell for its report",
                    font=("Arial", 9, "italic")).pack(side="left", padx=10)

        # A draggable split: the report needs a readable width, but how much
        # is readable depends on the window, so let the user decide.
        body = tk.PanedWindow(f, orient="horizontal", bg=self.theme["bg"],
                              sashwidth=7, sashrelief="raised", borderwidth=0,
                              sashpad=1)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        left = tk.Frame(body, bg=self.theme["bg"])
        self.map_fig = Figure(figsize=(9, 7), layout="constrained")
        self.map_ax = self.map_fig.add_subplot(111)
        self.map_fig.patch.set_facecolor(self.theme["bg"])
        self.map_canvas = FigureCanvasTkAgg(self.map_fig, left)
        self.map_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.map_canvas.mpl_connect("button_press_event", self._on_map_click)

        side = tk.Frame(body, bg=self.theme["panel"])

        head = tk.Frame(side, bg=self.theme["panel"])
        head.pack(fill="x", padx=6, pady=(6, 2))
        self.map_title = tk.Label(head, text="Selected universe",
                                  bg=self.theme["panel"], fg=self.theme["text"],
                                  font=("Arial", 11, "bold"))
        self.map_title.pack(side="left")
        tk.Button(head, text="Copy", command=lambda: self._copy(self.map_info),
                  bg=self.theme["accent"], fg="white",
                  font=("Arial", 8, "bold")).pack(side="right", padx=2)
        tk.Button(head, text="Full report \u2192", command=self._map_to_report,
                  bg=self.theme["highlight"], fg="white",
                  font=("Arial", 8, "bold")).pack(side="right", padx=2)

        self.map_info = self._scrolled_text(side)
        self.map_info.frame.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        body.add(left, minsize=360, stretch="always")
        body.add(side, minsize=300, width=470, stretch="never")

        self.draw_map()

    def _map_to_report(self):
        """Send the map selection to the Report tab and run the full census."""
        a, b = self._selected
        self.rep_a.delete(0, "end"); self.rep_a.insert(0, str(a))
        self.rep_b.delete(0, "end"); self.rep_b.insert(0, str(b))
        self.nb.select(1)
        self._do_report()

    def draw_map(self):
        try:
            a0, a1 = int(self.map_a0.get()), int(self.map_a1.get())
            b0, b1 = int(self.map_b0.get()), int(self.map_b1.get())
        except ValueError:
            messagebox.showerror("Universe Map", "Ranges must be integers.")
            return
        if a0 < 0 or b0 < 0:
            messagebox.showerror("Universe Map",
                                 "This family is defined for a, b >= 0.\n"
                                 "For b < 0 use the Report tab: the negation "
                                 "duality n -> -n relates it to +|b|.")
            return
        if a1 < a0 or b1 < b0 or (a1 - a0 + 1) * (b1 - b0 + 1) > 4000:
            messagebox.showerror("Universe Map",
                                 "Empty or oversized range (cap 4000 cells).")
            return

        view = self.map_view.get()
        self._grid_range = (a0, a1, b0, b1)
        self._busy(f"Classifying ({view}) ...")

        ax = self.map_ax
        ax.clear()
        ax.set_facecolor(self.theme["bg"])
        self._grid_cells.clear()

        na, nb = a1 - a0 + 1, b1 - b0 + 1
        total = na * nb
        annotate = total <= 400
        fs = max(6, min(11, 260 // max(na, nb)))

        cells = {(a, b): mv.classify(a, b)
                 for a in range(a0, a1 + 1) for b in range(b0, b1 + 1)}

        # "reduction target" colours the equivalence classes.  A class that
        # occupies a single visible cell carries no information -- it is just
        # "this universe is its own normal form" -- so those are greyed and
        # only the classes that actually group several cells get a colour.
        nf_colour = {}
        if view == "reduction target":
            from collections import Counter
            sizes = Counter(u.normal for u in cells.values())
            shared = [nf for nf, k in sizes.items() if k > 1]
            # Only as many classes as there are distinguishable colours: if we
            # recycled the palette, two unrelated classes would share a colour
            # and the view would assert something false.  The rest stay grey.
            shared.sort(key=lambda nf: (-sizes[nf], nf))
            cmap = matplotlib.colormaps.get_cmap("tab20")
            for i, nf in enumerate(shared[:20]):
                nf_colour[nf] = cmap(i)
            self._nf_hidden = max(0, len(shared) - 20)

        crossed = 0
        for (a, b), u in cells.items():
            face, edge, lw, label, tcol = self._cell_style(u, view, nf_colour)
            r = Rectangle((b - 0.5, a - 0.5), 1, 1, facecolor=face,
                          edgecolor=edge, linewidth=lw)
            ax.add_patch(r)
            self._grid_cells[(a, b)] = r

            if view == "open & minimal only" and label is None:
                # strike the cell out rather than merely dimming it
                crossed += 1
                ax.plot([b - 0.42, b + 0.42], [a - 0.42, a + 0.42],
                        color="#4a4a58", linewidth=0.7, zorder=2)
                ax.plot([b - 0.42, b + 0.42], [a + 0.42, a - 0.42],
                        color="#4a4a58", linewidth=0.7, zorder=2)
            elif annotate and label:
                ax.text(b, a, label, ha="center", va="center", fontsize=fs,
                        color=tcol, fontweight="bold", zorder=3)

        ax.set_xlim(b0 - 0.5, b1 + 0.5)
        ax.set_ylim(a1 + 0.5, a0 - 0.5)          # a increases downward
        ax.set_xlabel("b  (offset)", color=self.theme["text"])
        ax.set_ylabel("a  (multiplier)", color=self.theme["text"])
        ax.set_title(self._view_title(view), color=self.theme["text"],
                     fontsize=12, fontweight="bold")
        ax.tick_params(colors=self.theme["text"])
        if na <= 30:
            ax.set_yticks(range(a0, a1 + 1))
        if nb <= 30:
            ax.set_xticks(range(b0, b1 + 1))

        handles = self._view_legend(view, cells, nf_colour)
        if handles:
            ax.legend(handles=handles, loc="upper left",
                      bbox_to_anchor=(0, -0.09), fontsize=8,
                      facecolor=self.theme["panel"],
                      edgecolor=self.theme["text"],
                      labelcolor=self.theme["text"],
                      ncol=2 if len(handles) > 4 else 1)
        self.map_canvas.draw_idle()
        self._busy(self._view_summary(view, cells, total, crossed, nf_colour))

    # ---- per-view cell styling ---------------------------------------

    def _cell_style(self, u, view, nf_colour):
        """(facecolor, edgecolor, linewidth, label, textcolour) for one cell.

        A label of None in the "open & minimal only" view means "strike out".
        """
        bg = self.theme["bg"]

        if view == "knowledge tier":
            k = u.knowledge
            return (KNOWLEDGE_COLOUR[k], bg, 1.2, KNOWLEDGE_CODE[k], "#101020")

        if view == "open & minimal only":
            if u.knowledge == mv.Knowledge.OPEN:
                return ("#f2e14c", "#ffffff", 1.4, "?", "#101020")
            return ("#171722", bg, 1.0, None, "#4a4a58")

        if view == "reduction target":
            grouped = u.normal in nf_colour
            face = nf_colour[u.normal] if grouped else "#2b2b3a"
            # Mark the representative only inside a class we are actually
            # showing.  Most cells in a wide view are their own normal form,
            # so marking all of them would white out the whole grid.
            representative = grouped and (u.a, abs(u.b)) == u.normal
            return (face,
                    "#ffffff" if representative else bg,
                    2.2 if representative else 1.0,
                    f"{u.normal[0]}\u00b7{u.normal[1]}",
                    "#101020" if grouped else "#8a8a9a")

        # default: "family + fate" -- fill carries the FATE, the letter
        # carries the family, and the border carries the family colour.  This
        # is what separates 2x+2 (green, solved) from 6x+2 (yellow, open).
        return (FATE_COLOUR[u.fate], FAMILY_COLOUR[u.family], 2.0,
                mv.CODE[u.family], "#101020")

    def _view_title(self, view):
        return {
            "family + fate":
                "Family (letter) over proved fate (colour)",
            "knowledge tier":
                "How much is known:  K > D > =  >  ?",
            "open & minimal only":
                "Research view: everything solved or reducible is struck out",
            "reduction target":
                "Normal form: the largest equivalence classes in view",
        }.get(view, view)

    def _view_legend(self, view, cells, nf_colour):
        if view == "knowledge tier":
            return [Rectangle((0, 0), 1, 1, facecolor=KNOWLEDGE_COLOUR[k],
                              label=KNOWLEDGE_BLURB[k])
                    for k in mv.Knowledge.ORDER]

        if view == "open & minimal only":
            return [
                Rectangle((0, 0), 1, 1, facecolor="#f2e14c",
                          label="open AND minimal -- its own normal form"),
                Rectangle((0, 0), 1, 1, facecolor="#171722",
                          label="struck out: fate proved, or reducible to a "
                                "smaller universe"),
            ]

        if view == "reduction target":
            from collections import Counter
            sizes = Counter(u.normal for u in cells.values())
            shared = sorted(nf_colour, key=lambda nf: (-sizes[nf], nf))
            out = [Rectangle((0, 0), 1, 1, facecolor=nf_colour[nf],
                             label=f"{nf[0]}x{nf[1]:+d}  ({sizes[nf]} cells)")
                   for nf in shared[:8]]
            if len(shared) > 8:
                out.append(Rectangle((0, 0), 1, 1, facecolor="none",
                                     edgecolor="none",
                                     label=f"... {len(shared) - 8} more classes"))
            if getattr(self, "_nf_hidden", 0):
                out.append(Rectangle((0, 0), 1, 1, facecolor="#2b2b3a",
                                     label=f"{self._nf_hidden} smaller classes "
                                           f"(not coloured -- palette exhausted)"))
            out.append(Rectangle((0, 0), 1, 1, facecolor="#2b2b3a",
                                 label="grey = alone in view, or uncoloured; "
                                       "white border = class representative"))
            return out

        # family + fate: two legends' worth of information, so show the fate
        # colours and note that the letter is the family.
        out = [Rectangle((0, 0), 1, 1, facecolor=FATE_COLOUR[f],
                         label=FATE_BLURB[f])
               for f in (mv.Fate.CYCLIC, mv.Fate.DIVERGENT,
                         mv.Fate.TERMINAL, mv.Fate.OPEN)]
        LETTERS = [
            (mv.Family.CONSTANT,   FAMILY_BLURB[mv.Family.CONSTANT]),
            (mv.Family.PURE_SHAPE, FAMILY_BLURB[mv.Family.PURE_SHAPE]),
            (mv.Family.PARITY_RUNAWAY,
             "a + b odd, or b = 0 with odd part of a > 1"),
            (mv.Family.HALVING,    FAMILY_BLURB[mv.Family.HALVING]),
            (mv.Family.ATTRACTING, FAMILY_BLURB[mv.Family.ATTRACTING]),
            (mv.Family.DESCENT,    FAMILY_BLURB[mv.Family.DESCENT]),
            (mv.Family.PRIMITIVE,  FAMILY_BLURB[mv.Family.PRIMITIVE]),
        ]
        out += [Rectangle((0, 0), 1, 1, facecolor="none",
                          edgecolor=FAMILY_COLOUR[fam], linewidth=2,
                          label=f"{mv.CODE[fam]}  {blurb}")
                for fam, blurb in LETTERS]
        return out

    def _view_summary(self, view, cells, total, crossed, nf_colour=None):
        nf_colour = nf_colour or {}
        from collections import Counter
        if view == "knowledge tier" or view == "open & minimal only":
            c = Counter(u.knowledge for u in cells.values())
            mini = c[mv.Knowledge.OPEN]
            if view == "open & minimal only":
                return (f"{total} universes; {crossed} struck out, "
                        f"{mini} left standing ({100 * mini / total:.1f}%) "
                        f"-- limiting density 2/pi^2 = 20.26%")
            return ("  |  ".join(
                f"{KNOWLEDGE_CODE[k]} {c[k]}" for k in mv.Knowledge.ORDER)
                + f"   of {total}")
        if view == "reduction target":
            sizes = Counter(u.normal for u in cells.values())
            shared = [nf for nf, k in sizes.items() if k > 1]
            biggest = max(sizes.values())
            return (f"{total} universes collapse to {len(sizes)} normal forms; "
                    f"{len(shared)} classes group 2+ cells (largest {biggest}); "
                    f"the {len(nf_colour)} largest are coloured; "
                    f"white border = the representative")
        n_open = sum(1 for u in cells.values() if u.fate == mv.Fate.OPEN)
        return (f"{total} universes; {n_open} open "
                f"({100 * n_open / total:.1f}%) -- limiting density 1/3")

    def _on_map_click(self, event):
        if event.inaxes is not self.map_ax or event.xdata is None:
            return
        b, a = int(round(event.xdata)), int(round(event.ydata))
        a0, a1, b0, b1 = self._grid_range
        if not (a0 <= a <= a1 and b0 <= b <= b1):
            return
        self._selected = (a, b)
        u = mv.classify(a, b)
        self.map_title.config(text=f"Selected:  {u.label}")
        self._set_text(self.map_info, self._report_text(a, b, with_cycles=False))
        self.rep_a.delete(0, "end"); self.rep_a.insert(0, str(a))
        self.rep_b.delete(0, "end"); self.rep_b.insert(0, str(b))
        self._busy(f"selected {u.label} -- {u.family}, {u.fate}")

    # =================================================================
    # Tab 2 -- Report
    # =================================================================

    def _build_report_tab(self):
        f = self._frame("  Report  ")
        ctl = tk.Frame(f, bg=self.theme["bg"])
        ctl.pack(fill="x", padx=10, pady=8)

        self._label(ctl, "a =").pack(side="left")
        self.rep_a = self._entry(ctl, 3); self.rep_a.pack(side="left", padx=4)
        self._label(ctl, "b =").pack(side="left")
        self.rep_b = self._entry(ctl, 1); self.rep_b.pack(side="left", padx=4)
        self._label(ctl, "   census seeds 1..").pack(side="left")
        self.rep_seeds = self._entry(ctl, 2000); self.rep_seeds.pack(side="left", padx=4)
        self._button(ctl, "Analyse", self._do_report, accent=True).pack(side="left", padx=12)
        self._button(ctl, "Copy", lambda: self._copy(self.rep_text)).pack(side="left")

        self.rep_text = self._scrolled_text(f)
        self.rep_text.frame.pack(fill="both", expand=True, padx=10, pady=5)

    def _do_report(self):
        try:
            a, b = int(self.rep_a.get()), int(self.rep_b.get())
            seeds = int(self.rep_seeds.get())
        except ValueError:
            messagebox.showerror("Report", "a, b and the seed count must be integers.")
            return
        self.show_report(a, b, seeds)

    def show_report(self, a, b, seeds=2000):
        self._busy(f"analysing {a}x{b:+d}...")
        try:
            txt = self._report_text(a, b, with_cycles=True, seeds=seeds)
        except Exception as exc:                       # noqa: BLE001
            messagebox.showerror("Report", str(exc))
            self._busy("error")
            return
        self._set_text(self.rep_text, txt)
        self._busy(f"{a}x{b:+d} analysed")

    def _report_text(self, a, b, with_cycles=True, seeds=2000):
        u = mv.classify(a, b)
        L = []
        add = L.append
        add(f"  {u.label}          f(n) = n/2 if n even,  {a}n{b:+d} if n odd")
        add("=" * 74)
        add("")
        add(f"  family        {u.family}")
        add(f"  fate          {u.fate.upper()}"
            + ("   [PROVED -- see the paper]" if u.is_proved else "   [UNRESOLVED]"))
        add(f"  knowledge     {u.knowledge}")
        if u.conjecture:
            add(f"  conjecture    {u.conjecture}")
        add("")
        add("  why")
        for line in _wrap(u.reason, 66):
            add(f"      {line}")
        add("")
        add(f"  drift         {u.drift:.4f} per step   (sqrt(a)/2)")
        add(f"                {u.odd_drift:.4f} per odd step   (a/4; "
            f"{'contracting' if u.odd_drift < 1 else 'expanding'})")
        add("")
        add("  over Z")
        inv_pos, inv_neg = mv.half_line_invariance(a, b)
        add(f"      Z(>=1) invariant : {'yes' if inv_pos else 'no'}"
            f"    (criterion a + b >= 1;  here {a}{b:+d} = {a + b})")
        add(f"      Z(<=-1) invariant: {'yes' if inv_neg else 'no'}"
            f"    (criterion b <= a - 1;  here {b} vs {a - 1})")
        if not (inv_pos and inv_neg) and a >= 1:
            add(f"      only odd n with |n| <= {abs(b)}/{a} can change sign,")
            add(f"      so at most {-(-abs(b) // a)} integers of each sign ever cross.")
        add(f"      the negatives of {a}x{b:+d} are the positives of {a}x{-b:+d}")

        add("")
        add("  cycle through 1")
        per, idx = mv.one_is_periodic(a, b)
        if a >= 1 and b >= 1:
            tot = a + b
            p2 = tot > 0 and (tot & (tot - 1)) == 0
            if per:
                add(f"      1 IS on a cycle -- its orbit meets a power of two "
                    f"at step {idx}")
                add(f"      a + b = {tot}" +
                    ("  is a power of two (one-step case)" if p2
                     else "  is not a power of two, so the route is longer"))
            else:
                add(f"      1 is NOT on a cycle (its orbit never meets a "
                    f"power of two)")
        else:
            add("      criterion stated for a, b >= 1")

        add("")
        if b:
            add(f"  radical       rad(b) = {mv.radical(abs(b))}"
                f"{'  divides a  ->  scaled copy of ' + str(a) + 'x+1' if mv.reduces_to_offset_one(a, abs(b)) else '  does not divide a'}")
        add("")
        add(f"  normal form   {u.normal[0]}x{u.normal[1]:+d}"
            + ("   (already in normal form)" if (u.a, abs(u.b)) == u.normal else ""))
        if u.chain:
            add("")
            add("  reduction chain")
            for r in u.chain:
                add(f"      [{r.kind:^11}]  {r.src[0]}x{r.src[1]:+d}  -->  "
                    f"{r.dst[0]}x{r.dst[1]:+d}")
                for line in _wrap(r.note, 58):
                    add(f"                     {line}")
        add("")
        if u.attracting:
            add("  attracting primes   " +
                ", ".join(f"{p}^{e}" for p, e in sorted(u.attracting.items())))
            add("      every orbit is absorbed into the scaled copy; the graph")
            add("      is that copy with a forest of transients attached.")
        if u.repelling:
            add("  repelling primes    " +
                ", ".join(f"{p}^{e}" for p, e in sorted(u.repelling.items())))
            nstrata = 1
            for e in u.repelling.values():
                nstrata *= e + 1
            add(f"      min(v_p(n), v_p(b)) is conserved, so the state space")
            add(f"      splits into {nstrata} mutually unreachable strata.")
        if not u.attracting and not u.repelling:
            add("  attracting / repelling primes: none")
        if b:
            subs = {d: v for d, v in mv.sub_universes(a, abs(b)).items() if d > 1}
            if subs:
                add("")
                add("  embedded scaled copies (odd d | b)")
                for d, (sa, sb) in subs.items():
                    add(f"      {d}Z carries a copy of {sa}x{sb:+d}")
        if not with_cycles:
            add("")
            add("  (open the Report or Cycle Census tab for the cycle search)")
            return "\n".join(L)

        add("")
        add("-" * 74)
        add(f"  CYCLE CENSUS   seeds 1..{seeds}")
        add("-" * 74)
        if a == 0 and b == 0:
            add("  degenerate: every orbit reaches the fixed point 0")
            return "\n".join(L)
        cycles = mv.find_cycles(a, b, seed_max=seeds)
        if not cycles:
            add("  no cycle found in this window -- consistent with a runaway")
            add("  universe, or the basin simply misses the seed range.")
            return "\n".join(L)
        groups = mv.decompose_cycles(a, b, cycles)
        add(f"  {len(cycles)} cycle(s) found, in {len(groups)} stratum/strata")
        add("")
        for d, cs in groups.items():
            if d == 1:
                add(f"  stratum d = 1   ({len(cs)}) primitive cycles of {u.label}")
            else:
                add(f"  stratum d = {d}   ({len(cs)}) = {d} x primitive cycles "
                    f"of {a}x{abs(b) // d if b else 0:+d}")
            for c in cs:
                res = mv.cycle_equation_residual(c)
                mark = "ok" if res == 0 else f"RESIDUAL {res}"
                add(f"      period {c.length:<4} k={c.k:<3} m={c.m:<3} "
                    f"min={_fmt_int(c.minimum)}  max={_fmt_int(c.maximum)}  "
                    f"[cycle eq {mark}]")
                seq = " -> ".join(_fmt_int(x, 12) for x in c.elements[:10])
                if c.length > 10:
                    seq += f" -> ... (+{c.length - 10})"
                add(f"        {seq}")
            add("")
        add("  NOTE  these counts are lower bounds: a cycle whose basin misses")
        add("        the seed window is invisible to any such search.")
        return "\n".join(L)

    # =================================================================
    # Tab 3 -- Cycle Census
    # =================================================================

    def _build_cycles_tab(self):
        f = self._frame("  Cycle Census  ")
        ctl = tk.Frame(f, bg=self.theme["bg"])
        ctl.pack(fill="x", padx=10, pady=8)

        self._label(ctl, "a =").pack(side="left")
        self.cyc_a = self._entry(ctl, 3); self.cyc_a.pack(side="left", padx=4)
        self._label(ctl, "b from").pack(side="left")
        self.cyc_b0 = self._entry(ctl, 1); self.cyc_b0.pack(side="left", padx=4)
        self._label(ctl, "to").pack(side="left")
        self.cyc_b1 = self._entry(ctl, 49); self.cyc_b1.pack(side="left", padx=4)
        self._label(ctl, "   seeds 1..").pack(side="left")
        self.cyc_seeds = self._entry(ctl, 3000); self.cyc_seeds.pack(side="left", padx=4)
        self._button(ctl, "Run census", self._do_census, accent=True).pack(side="left", padx=12)

        # Grid container so the two scrollbars get their own cells; the
        # "periods" column is wider than any sane window, so the horizontal
        # bar is load-bearing here rather than decorative.
        holder = tk.Frame(f, bg=self.theme["bg"])
        holder.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("b", "total", "primitive", "normal", "strata", "periods")
        headings = {"b": "b", "total": "Cycles", "primitive": "Primitive",
                    "normal": "Normal form", "strata": "Strata",
                    "periods": "Periods"}
        self.cyc_tree = ttk.Treeview(holder, columns=cols, show="headings",
                                     height=18)
        for c, w in zip(cols, (60, 70, 90, 110, 70, 700)):
            self.cyc_tree.heading(c, text=headings[c])
            self.cyc_tree.column(c, width=w, minwidth=50, anchor="w",
                                 stretch=(c == "periods"))
        vsb = ttk.Scrollbar(holder, orient="vertical",
                            command=self.cyc_tree.yview,
                            style="MV.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(holder, orient="horizontal",
                            command=self.cyc_tree.xview,
                            style="MV.Horizontal.TScrollbar")
        self.cyc_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.cyc_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)

        # double-click a row to open that universe in the Report tab
        self.cyc_tree.bind("<Double-1>", self._census_open_row)

        self.cyc_note = self._label(
            f, "The total is the sum of the primitive counts of a*x+(b/d) over "
               "the divisors d | b  (divisor decomposition theorem).  "
               "Double-click a row for its full report.",
            font=("Arial", 9, "italic"))
        self.cyc_note.pack(anchor="w", padx=12, pady=(0, 8))

    def _do_census(self):
        try:
            a = int(self.cyc_a.get())
            b0, b1 = int(self.cyc_b0.get()), int(self.cyc_b1.get())
            seeds = int(self.cyc_seeds.get())
        except ValueError:
            messagebox.showerror("Cycle Census", "All fields must be integers.")
            return
        if b1 < b0 or b1 - b0 > 400:
            messagebox.showerror("Cycle Census", "Empty or oversized b range (cap 400).")
            return

        self.cyc_tree.delete(*self.cyc_tree.get_children())
        for b in range(b0, b1 + 1):
            if b == 0 and a == 0:
                continue
            self._busy(f"census {a}x{b:+d} ...")
            cs = mv.find_cycles(a, b, seed_max=seeds)
            groups = mv.decompose_cycles(a, b, cs)
            prim = sum(1 for c in cs if c.is_primitive)
            nf = mv.normal_form(a, b) if b else (mv.odd_part(a) if a else 0, 0)
            periods = ", ".join(str(c.length) for c in cs[:14])
            if len(cs) > 14:
                periods += " ..."
            self.cyc_tree.insert("", "end", values=(
                b, len(cs), prim,
                f"{nf[0]}x{nf[1]:+d}" if b else f"{nf[0]}x+0",
                len(groups), periods or "--"))
            self.update_idletasks()
        self._busy(f"census complete for {a}x+b, b in [{b0},{b1}]")

    def _census_open_row(self, _event=None):
        """Double-click: open the highlighted row's universe in Report."""
        sel = self.cyc_tree.selection()
        if not sel:
            return
        vals = self.cyc_tree.item(sel[0])["values"]
        try:
            a, b = int(self.cyc_a.get()), int(vals[0])
        except (ValueError, IndexError):
            return
        self.rep_a.delete(0, "end"); self.rep_a.insert(0, str(a))
        self.rep_b.delete(0, "end"); self.rep_b.insert(0, str(b))
        self.nb.select(1)
        self._do_report()

    # =================================================================
    # Tab 4 -- Symmetries
    # =================================================================

    def _build_symmetry_tab(self):
        f = self._frame("  Symmetries  ")
        ctl = tk.Frame(f, bg=self.theme["bg"])
        ctl.pack(fill="x", padx=10, pady=8)

        self._label(ctl, "a =").pack(side="left")
        self.sym_a = self._entry(ctl, 3); self.sym_a.pack(side="left", padx=4)
        self._label(ctl, "b =").pack(side="left")
        self.sym_b = self._entry(ctl, 1); self.sym_b.pack(side="left", padx=4)
        self._label(ctl, "   seed n =").pack(side="left")
        self.sym_n = self._entry(ctl, 7); self.sym_n.pack(side="left", padx=4)
        self._label(ctl, "   odd scale d =").pack(side="left")
        self.sym_d = self._entry(ctl, 5); self.sym_d.pack(side="left", padx=4)
        self._button(ctl, "Show", self._do_symmetry, accent=True).pack(side="left", padx=12)
        self._button(ctl, "Copy", lambda: self._copy(self.sym_text)).pack(side="left")

        self.sym_text = self._scrolled_text(f)
        self.sym_text.frame.pack(fill="both", expand=True, padx=10, pady=5)

    def _do_symmetry(self):
        try:
            a, b = int(self.sym_a.get()), int(self.sym_b.get())
            n, d = int(self.sym_n.get()), int(self.sym_d.get())
        except ValueError:
            messagebox.showerror("Symmetries", "All fields must be integers.")
            return
        if n < 1:
            messagebox.showerror("Symmetries", "The seed must be positive.")
            return
        if d % 2 == 0:
            messagebox.showerror(
                "Symmetries",
                "The scaling symmetry needs an ODD d.\n\n"
                "For even d it fails at the very first step: n and dn must "
                "have the same parity for the two maps to take the same "
                "branch.")
            return

        L = []
        add = L.append
        STEPS = 26

        add("=" * 78)
        add(f"  HALVING SYMMETRY      T_(2a,2b)  refines  T_(a,b)")
        add("=" * 78)
        add(f"  base      {a}x{b:+d}")
        add(f"  doubled   {2 * a}x{2 * b:+d}")
        add("")
        add("  For even n the two maps agree.  For odd n the doubled map goes")
        add("  n -> 2(an+b) -> an+b, taking one extra step through an even")
        add("  value that the base map skips.  Same orbit, more steps.")
        add("")
        t1, _ = mv.orbit(n, a, b, max_steps=STEPS)
        expect = []
        for x in t1:
            expect.append((x, False))
            if x % 2 == 1:
                expect.append((2 * mv.step(x, a, b), True))
        t2, _ = mv.orbit(n, 2 * a, 2 * b, max_steps=len(expect))
        add(f"  {'base ' + str(a) + 'x' + format(b, '+d'):<28}"
            f"{'doubled ' + str(2 * a) + 'x' + format(2 * b, '+d'):<28}")
        add(f"  {'-' * 26}  {'-' * 26}")
        i = 0
        for j, (val, inserted) in enumerate(expect):
            if j >= len(t2):
                break
            ok = "==" if t2[j] == val else "!!"
            if inserted:
                add(f"  {'':<26}  {_fmt_int(t2[j], 14):<20} {ok}  <- inserted")
            else:
                add(f"  {_fmt_int(t1[i], 14):<26}  {_fmt_int(t2[j], 14):<20} {ok}")
                i += 1
        agree = t2[:len(expect)] == [v for v, _ in expect][:len(t2)]
        add("")
        add(f"  the doubled orbit matches the predicted refinement: {agree}")
        add(f"  base steps shown {len(t1)}, doubled steps shown {len(t2)} "
            f"(+{len(t2) - len(t1)} inserted)")

        add("")
        add("=" * 78)
        add(f"  ODD SCALING SYMMETRY      T_(a,db)(d*n)  =  d * T_(a,b)(n)")
        add("=" * 78)
        add(f"  base      {a}x{b:+d}          seed {n}")
        add(f"  scaled    {a}x{d * b:+d}        seed {d * n}   (d = {d})")
        add("")
        s1, _ = mv.orbit(n, a, b, max_steps=STEPS)
        s2, _ = mv.orbit(d * n, a, d * b, max_steps=STEPS)
        add(f"  {'base':<28}{'scaled':<28}{'scaled / d'}")
        add(f"  {'-' * 26}  {'-' * 26}  {'-' * 12}")
        good = True
        for k in range(min(len(s1), len(s2))):
            q = s2[k] // d if d and s2[k] % d == 0 else None
            ok = (q == s1[k])
            good &= ok
            add(f"  {_fmt_int(s1[k], 14):<26}  {_fmt_int(s2[k], 14):<26}  "
                f"{_fmt_int(q, 12) if q is not None else '--':<12} "
                f"{'==' if ok else '!!'}")
        add("")
        add(f"  the scaled orbit is exactly d times the base orbit: {good}")
        u = mv.classify(a, d * b)
        add("")
        if any(p in u.attracting for p in mv.factorise(d) if p != 2):
            add(f"  {d} shares a prime with a = {a}, so this copy is ATTRACTING:")
            add(f"  every orbit of {a}x{d * b:+d} eventually falls into it.")
        else:
            add(f"  {d} shares no prime with a = {a}, so this copy is REPELLING:")
            add(f"  the multiples of {d} form a stratum that nothing outside it")
            add(f"  can ever enter, and nothing inside can ever leave.")

        self._set_text(self.sym_text, "\n".join(L))
        self._busy("symmetries shown")

    # =================================================================
    # Tab 5 -- Heat Maps
    # =================================================================

    def _build_heat_tab(self):
        f = self._frame("  Heat Maps  ")
        ctl = tk.Frame(f, bg=self.theme["bg"])
        ctl.pack(fill="x", padx=10, pady=8)

        self._label(ctl, "metric").pack(side="left")
        self.heat_metric = ttk.Combobox(
            ctl, width=26, state="readonly",
            values=["average relative peak", "average path length",
                    "cycle count", "drift a/4 per odd step"])
        self.heat_metric.current(0)
        self.heat_metric.pack(side="left", padx=6)

        self._label(ctl, "  a<=").pack(side="left")
        self.heat_a = self._entry(ctl, 8, 5); self.heat_a.pack(side="left", padx=3)
        self._label(ctl, "b<=").pack(side="left")
        self.heat_b = self._entry(ctl, 8, 5); self.heat_b.pack(side="left", padx=3)
        self._label(ctl, "  seeds 1..").pack(side="left")
        self.heat_n = self._entry(ctl, 400, 7); self.heat_n.pack(side="left", padx=3)
        self._button(ctl, "Compute", self._do_heat, accent=True).pack(side="left", padx=12)
        self._label(ctl, "(large ranges are slow -- this is a real search)",
                    font=("Arial", 8, "italic")).pack(side="left")

        self.heat_fig = Figure(figsize=(10, 7), layout="constrained")
        self.heat_ax = self.heat_fig.add_subplot(111)
        self.heat_fig.patch.set_facecolor(self.theme["bg"])
        self.heat_canvas = FigureCanvasTkAgg(self.heat_fig, f)
        self.heat_canvas.get_tk_widget().pack(fill="both", expand=True,
                                              padx=10, pady=5)

    def _do_heat(self):
        try:
            amax, bmax = int(self.heat_a.get()), int(self.heat_b.get())
            nmax = int(self.heat_n.get())
        except ValueError:
            messagebox.showerror("Heat Maps", "All fields must be integers.")
            return
        if amax < 0 or bmax < 0 or (amax + 1) * (bmax + 1) > 900:
            messagebox.showerror("Heat Maps", "Range must be non-negative and "
                                              "at most 900 cells.")
            return

        metric = self.heat_metric.get()
        vals, labels = {}, {}
        total = (amax + 1) * (bmax + 1)
        done = 0
        for a in range(amax + 1):
            for b in range(bmax + 1):
                done += 1
                if done % 5 == 0:
                    self._busy(f"computing {metric}: {done}/{total} ...")
                if metric == "drift a/4 per odd step":
                    v = mv.classify(a, b).odd_drift
                    vals[(a, b)] = v
                    labels[(a, b)] = f"{v:.2f}"
                elif metric == "cycle count":
                    if a == 0 and b == 0:
                        vals[(a, b)] = None; labels[(a, b)] = "--"
                        continue
                    cs = mv.find_cycles(a, b, seed_max=min(nmax, 2000),
                                        max_steps=20000)
                    vals[(a, b)] = len(cs) if cs else None
                    labels[(a, b)] = str(len(cs)) if cs else "0"
                else:
                    st = mv.growth_statistics(a, b, n_max=nmax, max_steps=1500,
                                              value_cap=10 ** 24)
                    key = "peak" if metric.endswith("peak") else "path"
                    v = st[key]
                    vals[(a, b)] = v
                    labels[(a, b)] = "RUN" if v is None else (
                        f"{v:.2f}" if key == "peak" else f"{v:.0f}")

        finite = [v for v in vals.values() if v is not None]
        lo, hi = (min(finite), max(finite)) if finite else (0, 1)
        cmap = matplotlib.colormaps.get_cmap("viridis")

        ax = self.heat_ax
        ax.clear()
        ax.set_facecolor(self.theme["bg"])
        for (a, b), v in vals.items():
            if v is None:
                col = "#5a1d1d"
            else:
                t = 0.0 if hi == lo else (v - lo) / (hi - lo)
                col = cmap(t)
            ax.add_patch(Rectangle((b - 0.5, a - 0.5), 1, 1, facecolor=col,
                                   edgecolor=self.theme["bg"], linewidth=1))
            if total <= 200:
                ax.text(b, a, labels[(a, b)], ha="center", va="center",
                        fontsize=7, color="white")
        ax.set_xlim(-0.5, bmax + 0.5)
        ax.set_ylim(amax + 0.5, -0.5)
        ax.set_xticks(range(bmax + 1)); ax.set_yticks(range(amax + 1))
        ax.set_xlabel("b", color=self.theme["text"])
        ax.set_ylabel("a", color=self.theme["text"])
        ax.set_title(f"{metric}   (seeds 1..{nmax};  dark red = runaway)",
                     color=self.theme["text"], fontsize=12, fontweight="bold")
        ax.tick_params(colors=self.theme["text"])
        self.heat_canvas.draw_idle()
        self._busy(f"{metric}: range [{lo:.3f}, {hi:.3f}] over {len(finite)} "
                   f"non-runaway cells")


    # =================================================================
    # Tab 6 -- q-ary maps  (mod q instead of mod 2)
    # =================================================================

    QARY_PRESETS = {
        "3x+1  (q=2, classical)":            (2, "3", "1"),
        "5x+1  (q=2, expanding)":            (2, "5", "1"),
        "2x+1  (q=2, escaping residue)":     (2, "2", "1"),
        "q=3, contracting (0% runaway)":     (3, "5 3", "3 3"),
        "q=3, expanding (48% runaway)":      (3, "5 7", "1 1"),
        "q=3, drift says contract but ALL":  (3, "3 3", "1 1"),
        "q=5, a=(3,3,3,3)":                  (5, "3 3 3 3", "1 1 1 1"),
    }

    def _build_qary_tab(self):
        f = self._frame("  q-ary Maps  ")

        ctl = tk.Frame(f, bg=self.theme["bg"])
        ctl.pack(fill="x", padx=10, pady=(8, 2))
        self._label(ctl, "preset").pack(side="left")
        self.q_preset = ttk.Combobox(ctl, width=30, state="readonly",
                                     values=list(self.QARY_PRESETS))
        self.q_preset.current(0)
        self.q_preset.pack(side="left", padx=6)
        self.q_preset.bind("<<ComboboxSelected>>", self._qary_load_preset)

        ctl2 = tk.Frame(f, bg=self.theme["bg"])
        ctl2.pack(fill="x", padx=10, pady=(0, 6))
        self._label(ctl2, "q =").pack(side="left")
        self.q_q = self._entry(ctl2, 2, 4); self.q_q.pack(side="left", padx=4)
        self._label(ctl2, "  a_1..a_(q-1) =").pack(side="left")
        self.q_a = self._entry(ctl2, "3", 18); self.q_a.pack(side="left", padx=4)
        self._label(ctl2, "  b_1..b_(q-1) =").pack(side="left")
        self.q_b = self._entry(ctl2, "1", 18); self.q_b.pack(side="left", padx=4)
        self._label(ctl2, "  seeds 1..").pack(side="left")
        self.q_seeds = self._entry(ctl2, 2000, 8); self.q_seeds.pack(side="left", padx=4)
        self._button(ctl2, "Analyse", self._do_qary, accent=True).pack(side="left", padx=10)
        self._button(ctl2, "Copy", lambda: self._copy(self.q_text)).pack(side="left")

        body = tk.PanedWindow(f, orient="horizontal", bg=self.theme["bg"],
                              sashwidth=7, sashrelief="raised", borderwidth=0)
        body.pack(fill="both", expand=True, padx=10, pady=5)

        left = tk.Frame(body, bg=self.theme["bg"])
        self.q_fig = Figure(figsize=(6, 5.5), layout="constrained")
        self.q_ax = self.q_fig.add_subplot(111)
        self.q_fig.patch.set_facecolor(self.theme["bg"])
        self.q_canvas = FigureCanvasTkAgg(self.q_fig, left)
        self.q_canvas.get_tk_widget().pack(fill="both", expand=True)

        right = tk.Frame(body, bg=self.theme["panel"])
        self.q_text = self._scrolled_text(right)
        self.q_text.frame.pack(fill="both", expand=True, padx=6, pady=6)

        body.add(left, minsize=340, stretch="always")
        body.add(right, minsize=340, width=560, stretch="always")

        self._do_qary()

    def _qary_load_preset(self, _e=None):
        q, a, b = self.QARY_PRESETS[self.q_preset.get()]
        for w, v in ((self.q_q, q), (self.q_a, a), (self.q_b, b)):
            w.delete(0, "end"); w.insert(0, str(v))
        self._do_qary()

    def _parse_qary(self):
        q = int(self.q_q.get())
        a = [int(x) for x in self.q_a.get().replace(",", " ").split()]
        b = [int(x) for x in self.q_b.get().replace(",", " ").split()]
        return qa.QMap(q, a, b)

    def _do_qary(self):
        try:
            m = self._parse_qary()
            seeds = int(self.q_seeds.get())
        except ValueError as exc:
            messagebox.showerror("q-ary Maps",
                                 f"{exc}\n\nGive q, then q-1 multipliers and "
                                 f"q-1 offsets, space separated.")
            return
        self._busy(f"analysing q={m.q} ...")

        g = qa.residue_graph(m)
        esc = qa.escaping_residues(m)
        L = []
        add = L.append
        add(f"  q = {m.q}")
        for i in range(1, m.q):
            add(f"     n = {i} (mod {m.q}):  n -> {m.a[i-1]}n{m.b[i-1]:+d}")
        add(f"     n = 0 (mod {m.q}):  n -> n/{m.q}")
        add("")
        add("=" * 66)
        add("  RESIDUE GRAPH      tau(i) = a_i*i + b_i  (mod q)")
        add("=" * 66)
        add("  the affine branches move the residue deterministically;")
        add("  the dividing branch does not, since n/q depends on n mod q^2.")
        add("")
        for i in range(1, m.q):
            mark = "  <-- ESCAPING" if i in esc else ""
            add(f"     {i} -> {g[i]}{mark}")
        add("")
        if esc:
            add(f"  escaping residues: {esc}")
            add("  an orbit entering one of these never meets the dividing")
            add("  branch again.")
            grows = []
            for r in esc:
                vis = set(); j = r
                while j not in vis:
                    vis.add(j); j = g[j]
                ok = all(m.a[k-1] >= 2 or (m.a[k-1] == 1 and m.b[k-1] >= 1)
                         for k in vis)
                grows.append((r, ok, sorted(vis)))
            for r, ok, vis in grows:
                if ok:
                    add(f"     residue {r}: every branch on its cycle {vis} grows,")
                    add(f"        so every n = {r} (mod {m.q}) DIVERGES.")
                else:
                    add(f"     residue {r}: some branch on {vis} does not grow")
                    add(f"        (identity or constant), so no divergence claim.")
        else:
            add("  no escaping residues: every class can reach the divider.")
        add("")
        add("=" * 66)
        add("  DRIFT")
        add("=" * 66)
        prod = 1
        for x in m.a:
            prod *= abs(x)
        thr = qa.qary_drift_threshold(m.q)
        d = qa.qary_drift(m)
        add(f"     prod a_i = {prod}      threshold q^q = {thr}")
        add(f"     delta    = {d:.4f} per affine step")
        add(f"     => heuristically {'CONTRACTING' if prod < thr else 'EXPANDING'}")
        add("     (a heuristic only: it assumes the residues equidistribute)")
        if esc:
            add("")
            add("  CAUTION: this map has escaping residues, which is exactly")
            add("  the configuration that breaks equidistribution.  The")
            add("  obstruction is a theorem and the drift is not, so the")
            add("  obstruction wins: orbits in an escaping class diverge no")
            add("  matter what the drift says.")

        add("")
        add("=" * 66)
        add("  SYMMETRIES")
        add("=" * 66)
        m2 = m.scaled(m.q)
        add(f"  q-scaling: multiplying every coefficient by q = {m.q} gives")
        add(f"     a = {m2.a},  b = {m2.b}")
        add("     which traverses the same orbits with one extra division")
        add("     inserted after each affine step.  Check on n = 1..6:")
        for x in range(1, 7):
            add(f"        n={x}: base -> {m.step(x):<8} scaled -> {m2.step(x):<8}"
                f" scaled^2 -> {m2.step(m2.step(x))}")
        ds = [d for d in range(2, 2 * m.q) if __import__("math").gcd(d, m.q) == 1]
        if ds:
            dd = ds[0]
            md = m.offset_scaled(dd)
            add("")
            add(f"  twisted scaling by d = {dd} (coprime to q): n -> {dd}n")
            add(f"     permutes the branches, giving a = {md.a}, b = {md.b}")
            add("     Check:")
            for x in range(1, 6):
                add(f"        d*T(n={x}) = {dd * m.step(x):<10} "
                    f"T'({dd}*{x}) = {md.step(dd * x)}")
            add("     Note the multipliers move with the branches: this is why")
            add("     rigidity FAILS for q >= 3 and there is no normal form.")

        add("")
        add("=" * 66)
        add(f"  CYCLE CENSUS   seeds 1..{seeds}")
        add("=" * 66)
        found = {}
        escaped = 0
        for x in range(1, seeds + 1):
            t, ci = m.orbit(x, max_steps=4000, value_cap=10 ** 40)
            if ci is None:
                escaped += 1
                continue
            c = tuple(sorted(t[ci:]))
            found[c] = found.get(c, 0) + 1
        add(f"     {escaped} of {seeds} seeds left the budget (runaway)")
        add(f"     {len(found)} distinct cycle(s)")
        for c, k in sorted(found.items(), key=lambda kv: -kv[1])[:12]:
            shown = list(c[:10])
            more = "" if len(c) <= 10 else f" ... (+{len(c)-10})"
            add(f"        period {len(c):<4} basin {k:<6} {shown}{more}")

        self._set_text(self.q_text, "\n".join(L))
        self._draw_residue_graph(m, g, esc)
        note = ""
        if len(esc) == m.q - 1:
            note = "  -- ALL residues escape, so the drift is irrelevant"
        elif esc and prod < thr:
            note = "  -- drift says contract, but some residues escape"
        self._busy(f"q={m.q}: {len(esc)} escaping residue(s), "
                   f"prod a_i = {prod} vs q^q = {thr}, "
                   f"{len(found)} cycle(s){note}")

    def _draw_residue_graph(self, m, g, esc):
        """Residues on a circle, arrows i -> tau(i).  Theorem 'residue
        obstruction' is visible here: an escaping residue is one whose forward
        path never reaches the node 0."""
        import math as _m
        ax = self.q_ax
        ax.clear()
        ax.set_facecolor(self.theme["bg"])
        q = m.q
        pos = {i: (_m.cos(2 * _m.pi * i / q - _m.pi / 2),
                   _m.sin(2 * _m.pi * i / q - _m.pi / 2)) for i in range(q)}

        for i in range(1, q):
            x0, y0 = pos[i]
            x1, y1 = pos[g[i]]
            col = "#e0736f" if i in esc else "#5fb36a"
            if i == g[i]:
                # a self-loop: a small circle sitting just outside the node,
                # with an arrowhead so the direction is still readable
                cx, cy = x0 * 1.22, y0 * 1.22
                loop = Circle((cx, cy), 0.115, fill=False, edgecolor=col,
                              lw=2, zorder=2)
                ax.add_patch(loop)
                ax.annotate("", xy=(cx - 0.02, cy - 0.113),
                            xytext=(cx + 0.06, cy - 0.10),
                            arrowprops=dict(arrowstyle="-|>", color=col, lw=2))
            else:
                ax.annotate("", xy=(x1 * 0.86, y1 * 0.86), xytext=(x0 * 0.86, y0 * 0.86),
                            arrowprops=dict(arrowstyle="-|>", color=col, lw=2,
                                            connectionstyle="arc3,rad=0.18"))
        for i in range(q):
            x, y = pos[i]
            if i == 0:
                fc, ec, tc = "#7fb3e8", "#ffffff", "#101020"
            elif i in esc:
                fc, ec, tc = "#e0736f", self.theme["bg"], "#101020"
            else:
                fc, ec, tc = "#f2e14c", self.theme["bg"], "#101020"
            ax.plot([x], [y], "o", ms=30, color=fc, markeredgecolor=ec,
                    markeredgewidth=2, zorder=3)
            ax.text(x, y, str(i), ha="center", va="center", fontsize=11,
                    fontweight="bold", color=tc, zorder=4)

        ax.set_xlim(-1.45, 1.45); ax.set_ylim(-1.45, 1.45)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"Residue graph mod {q}:  blue = the dividing class,\n"
                     f"red = escaping (can never divide again)",
                     color=self.theme["text"], fontsize=11, fontweight="bold")
        self.q_canvas.draw_idle()

    # =================================================================
    # Tab 7 -- beyond modularity: predicate-driven maps
    # =================================================================

    def _build_predicate_tab(self):
        f = self._frame("  Beyond Modularity  ")

        ctl = tk.Frame(f, bg=self.theme["bg"])
        ctl.pack(fill="x", padx=10, pady=8)
        self._label(ctl, "map").pack(side="left")
        self.p_choice = ttk.Combobox(
            ctl, width=46, state="readonly",
            values=["primality:  3n+1 if prime, n/2 if even, n+1 otherwise",
                    "congruence control:  n/2 if even, n+1 if odd  (= x+1)",
                    "congruence control:  n/2 if even, 3n+1 if odd (= 3x+1)"])
        self.p_choice.current(0)
        self.p_choice.pack(side="left", padx=6)
        self._label(ctl, "  seeds 1..").pack(side="left")
        self.p_seeds = self._entry(ctl, 20000, 9); self.p_seeds.pack(side="left", padx=4)
        self._button(ctl, "Run", self._do_predicate, accent=True).pack(side="left", padx=10)
        self._button(ctl, "Copy", lambda: self._copy(self.p_text)).pack(side="left")

        self.p_text = self._scrolled_text(f)
        self.p_text.frame.pack(fill="both", expand=True, padx=10, pady=5)

    def _predicate_map(self):
        i = self.p_choice.current()
        if i == 1:
            return qa.PredicateMap([
                ("even", lambda n: n % 2 == 0, lambda n: n // 2),
                ("odd", lambda n: True, lambda n: n + 1)]), None
        if i == 2:
            return qa.PredicateMap([
                ("even", lambda n: n % 2 == 0, lambda n: n // 2),
                ("odd", lambda n: True, lambda n: 3 * n + 1)]), None
        return qa.primality_map(), "prime"

    def _do_predicate(self):
        import math as _m
        try:
            seeds = int(self.p_seeds.get())
        except ValueError:
            messagebox.showerror("Beyond Modularity", "Seeds must be an integer.")
            return
        pm, growth_branch = self._predicate_map()
        self._busy("running predicate map ...")

        L = []
        add = L.append
        add("=" * 70)
        add("  " + self.p_choice.get())
        add("=" * 70)
        add("  A predicate map picks its branch by a property of n, not by a")
        add("  congruence.  When the predicate IS a congruence the map is a")
        add("  q-ary map in disguise and the whole theory applies; when it is")
        add("  not -- primality here -- none of it does.")
        add("")

        found = {}
        failed = 0
        for x in range(1, seeds + 1):
            t, ci = pm.orbit(x, max_steps=4000, value_cap=10 ** 30)
            if ci is None:
                failed += 1
                continue
            found[tuple(sorted(t[ci:]))] = found.get(tuple(sorted(t[ci:])), 0) + 1
        add(f"  seeds 1..{seeds}:  {failed} failed to cycle")
        add(f"  distinct cycles: {len(found)}")
        for c, k in sorted(found.items(), key=lambda kv: -kv[1]):
            shown = list(c[:14])
            more = "" if len(c) <= 14 else f" ... (+{len(c)-14})"
            add(f"     period {len(c):<4} basin {k:<7} ({100*k/max(seeds,1):.1f}%)"
                f"  {shown}{more}")

        if growth_branch == "prime":
            add("")
            add("=" * 70)
            add("  THE DENSITY BUDGET")
            add("=" * 70)
            add("  Growth happens only at primes:")
            add("     odd prime p    ->  (3p+1)/2  ~ 1.5 p")
            add("     odd composite m->  (m+1)/2   ~ 0.5 m")
            thr = _m.log(2) / _m.log(3)
            add(f"  so divergence needs the odd values visited to be prime with")
            add(f"  density r satisfying (3/2)^r (1/2)^(1-r) > 1, i.e.")
            add(f"     r > ln2/ln3 = {thr:.5f}   ({100*thr:.2f}%)")
            add("")
            add("  Measured density of primes among odd TRANSIENT values")
            add("  (cycles excluded -- they are short and prime-rich, and")
            add("   counting them makes the density look alarmingly high).")
            add("  Each row is its own block of seeds, drawn just above its")
            add("  floor, so the counts are NOT nested -- only the densities")
            add("  are comparable down the column:")
            add("")
            add(f"     {'above':>12} {'odd seen':>10} {'prime':>8} {'density':>9}"
                f" {'1/ln n':>9}")
            # each row is its OWN block of seeds, drawn just above the floor
            # it reports: an orbit from a small seed never reaches 1e8, so a
            # single seed range cannot fill this table.  Same bands as
            # PRIME_BANDS in Multiverse/generate_data.py, which produces the
            # version of this table printed in the paper.
            for lo, hi, floor in [(1, 4000, 10 ** 3),
                                  (10 ** 5, 10 ** 5 + 2500, 10 ** 4),
                                  (10 ** 7, 10 ** 7 + 1800, 10 ** 6),
                                  (10 ** 9, 10 ** 9 + 1200, 10 ** 8),
                                  (10 ** 12, 10 ** 12 + 900, 10 ** 11)]:
                tot = pr = 0
                stp = max(1, (hi - lo) // 900)
                for sdd in range(lo, hi, stp):
                    t, ci = pm.orbit(sdd, max_steps=6000, value_cap=10 ** 40)
                    seg = t[:ci] if ci is not None else t
                    for y in seg:
                        if y % 2 == 1 and y > floor:
                            tot += 1
                            pr += qa.is_prime(y)
                dens = 100 * pr / max(tot, 1)
                ref = 100 / _m.log(max(floor, 3))
                add(f"     {floor:>12} {tot:>10} {pr:>8} {dens:>8.2f}% {ref:>8.2f}%")
                self.update_idletasks()
            add("")
            add("  The density decays, but sits 2-3x above the 1/ln n a random")
            add("  integer would give: the map's odd values really are biased")
            add("  towards primes.  It is still nowhere near the 63.09% needed,")
            add("  and it is falling -- so every orbit should be periodic.")
            add("  That is Conjecture 'primality map' in the paper; it is not")
            add("  proved, because it is a statement about the invariant")
            add("  measure of the map, not about the density of primes in N.")

        self._set_text(self.p_text, "\n".join(L))
        self._busy(f"{len(found)} cycle(s), {failed} non-cycling of {seeds} seeds")


def _wrap(text, width):
    """Minimal greedy wrap -- avoids importing textwrap for three call sites."""
    words, line, out = text.split(), "", []
    for w in words:
        if len(line) + len(w) + 1 > width and line:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out or [""]


def open_multiverse(parent):
    """Entry point used by Collatz_Program.py."""
    win = MultiverseWindow(parent)
    win.transient(parent)
    return win
