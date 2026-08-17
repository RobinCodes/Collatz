import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.animation import FuncAnimation
from collections import defaultdict, Counter
import json
from datetime import datetime


# ======================================================
# Visual Configuration
# ======================================================

THEMES = {
    "Deep Space": {
        "bg": "#050b1e",
        "panel": "#0b1633",
        "accent": "#143a8f",
        "text": "#c7d4ff",
        "highlight": "#2e7ddf"
    },
    "Cyber Neon": {
        "bg": "#0a0e27",
        "panel": "#1a1f3a",
        "accent": "#ff006e",
        "text": "#00f5ff",
        "highlight": "#7209b7"
    },
    "Forest": {
        "bg": "#0d1b0d",
        "panel": "#1a331a",
        "accent": "#2d5016",
        "text": "#b8e6b8",
        "highlight": "#4d7c0f"
    }
}

REF_POINTS = 200
NODE_MIN, NODE_MAX = 20, 120
GLOW_MIN, GLOW_MAX = 300, 1400
LABEL_MIN, LABEL_MAX = 6, 12


# ======================================================
# Mathematics & Analysis
# ======================================================

def parse_map(expr):
    """Parse generalized Collatz map: ax+b"""
    expr = expr.replace(" ", "")
    m = re.fullmatch(r'([+-]?\d*)x([+-]\d+)?', expr)
    if not m:
        raise ValueError(f"Invalid map: {expr}")
    a_str, b_str = m.groups()
    a = 1 if a_str in ("", "+") else -1 if a_str == "-" else int(a_str)
    b = int(b_str) if b_str else 0
    return a, b


def collatz_orbit(start, a, b, max_steps):
    """Compute orbit with cycle detection"""
    seen = {}
    seq = []
    n = start

    for step in range(max_steps):
        if n in seen:
            cycle_start = seen[n]
            return seq, seq[cycle_start:], True
        seen[n] = step
        seq.append(n)
        
        # Next iteration
        if n % 2 == 0:
            n = n // 2
        else:
            n = a * n + b
            
        if n <= 0:
            break

    return seq, [], False


def safe_mean(values):
    """Calculate mean using Python native operations for large numbers"""
    if not values:
        return 0
    return sum(values) / len(values)


def safe_median(values):
    """Calculate median using Python native operations"""
    if not values:
        return 0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 0:
        return (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
    else:
        return sorted_vals[n//2]


def safe_std(values):
    """Calculate standard deviation using Python native operations"""
    if not values:
        return 0
    mean = safe_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def analyze_sequence(seq, cycle, cycled):
    """Deep statistical analysis of a sequence"""
    if not seq:
        return {}
    
    analysis = {
        "length": len(seq),
        "max_value": max(seq),
        "min_value": min(seq),
        "start_value": seq[0],
        "end_value": seq[-1],
        "mean": safe_mean(seq),
        "median": safe_median(seq),
        "std_dev": safe_std(seq),
        "growth_rate": seq[-1] / seq[0] if seq[0] != 0 else 0,
        "cycled": cycled,
        "cycle_length": len(cycle) if cycled else 0,
        "even_count": sum(1 for x in seq if x % 2 == 0),
        "odd_count": sum(1 for x in seq if x % 2 == 1),
    }
    
    # Peak analysis
    peaks = []
    for i in range(1, len(seq) - 1):
        if seq[i] > seq[i-1] and seq[i] > seq[i+1]:
            peaks.append(seq[i])
    analysis["peak_count"] = len(peaks)
    analysis["peak_max"] = max(peaks) if peaks else 0
    
    # Trajectory classification
    if cycled:
        analysis["trajectory"] = "Cyclic"
    elif len(seq) >= 300:  # Max steps reached
        analysis["trajectory"] = "Divergent/Runaway"
    elif seq[-1] <= 0:
        analysis["trajectory"] = "Collapsed"
    else:
        analysis["trajectory"] = "Terminated"
    
    return analysis


# ======================================================
# Advanced Configuration Modal
# ======================================================

class AdvancedConfigModal(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Advanced Configuration")
        self.configure(bg=parent.theme["bg"])
        self.geometry("700x500")
        self.resizable(True, True)
        
        self.parent = parent
        self.theme = parent.theme
        self.result = None
        
        self._build_ui()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
    def _build_ui(self):
        # Instructions
        instructions = tk.Label(
            self, 
            text="Define specific map-start combinations (one per line):\nFormat: map_expression : start_values\nExample: 3x+1 : 7 15 27",
            bg=self.theme["bg"],
            fg=self.theme["text"],
            font=("Arial", 10),
            justify="left"
        )
        instructions.pack(padx=10, pady=10, anchor="w")
        
        # Text area
        text_frame = tk.Frame(self, bg=self.theme["bg"])
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_area = scrolledtext.ScrolledText(
            text_frame,
            bg=self.theme["panel"],
            fg="white",
            font=("Consolas", 10),
            insertbackground="white"
        )
        self.text_area.pack(fill="both", expand=True)
        
        # Example text
        example = """3x+1 : 7 15 27 63
5x+1 : 3 7 11
7x+1 : 5 9 13 17"""
        self.text_area.insert("1.0", example)
        
        # Buttons
        button_frame = tk.Frame(self, bg=self.theme["bg"])
        button_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(
            button_frame,
            text="Apply",
            command=self._apply,
            bg=self.theme["accent"],
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).pack(side="left", padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel,
            bg=self.theme["panel"],
            fg=self.theme["text"],
            font=("Arial", 10),
            width=15
        ).pack(side="left", padx=5)
        
    def _apply(self):
        """Parse and validate the configuration"""
        text = self.text_area.get("1.0", "end-1c")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        config = []
        try:
            for line in lines:
                if ":" not in line:
                    raise ValueError(f"Invalid format: {line}")
                
                map_part, starts_part = line.split(":", 1)
                map_expr = map_part.strip()
                starts = [int(x.strip()) for x in starts_part.split()]
                
                # Validate map
                a, b = parse_map(map_expr)
                
                config.append(((a, b), starts))
                
            self.result = config
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Invalid Configuration", 
                               f"Error parsing configuration:\n{str(e)}")
    
    def _cancel(self):
        self.result = None
        self.destroy()


# ======================================================
# Main Application
# ======================================================

class CollatzVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Advanced Collatz Orbital Analyzer")
        self._maximize()

        self.current_theme = "Deep Space"
        self.theme = THEMES[self.current_theme]
        self.configure(bg=self.theme["bg"])

        self.animation = None
        self.animate_var = tk.BooleanVar(value=False)  # Fixed: proper BooleanVar
        self.show_labels = tk.BooleanVar(value=False)
        self.show_grid = tk.BooleanVar(value=True)
        self.show_peaks = tk.BooleanVar(value=False)
        self.log_scale = tk.BooleanVar(value=True)
        self.results = defaultdict(list)
        self.analyses = defaultdict(list)
        self.advanced_config = None

        self._configure_styles()
        self._build_ui()

    def _maximize(self):
        """Maximize the window, whichever of the platform tricks actually works."""
        try:
            self.state('zoomed')  # Windows / some Linux window managers
            return
        except tk.TclError:
            pass
        try:
            self.attributes('-zoomed', True)  # X11
            return
        except tk.TclError:
            pass
        # Wayland and anything else: just size to the screen
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

    # Styling
    # --------------------------------------------------

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("default")

        style.configure("TNotebook", background=self.theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.theme["panel"], 
                       foreground=self.theme["text"], padding=8)
        style.map("TNotebook.Tab",
                 background=[("selected", self.theme["accent"])],
                 foreground=[("selected", "white")])

        style.configure("Treeview", background=self.theme["panel"],
                       foreground="white", fieldbackground=self.theme["panel"],
                       borderwidth=0)
        style.configure("Treeview.Heading", background=self.theme["accent"],
                       foreground="white")

    # --------------------------------------------------
    # UI Construction
    # --------------------------------------------------

    def _build_ui(self):
        # Top control panel
        control_frame = tk.Frame(self, bg=self.theme["bg"])
        control_frame.pack(fill="x", padx=15, pady=10)

        # Left controls
        left_frame = tk.Frame(control_frame, bg=self.theme["bg"])
        left_frame.pack(side="left", fill="both", expand=True)

        self._create_input_section(left_frame)
        
        # Right controls
        right_frame = tk.Frame(control_frame, bg=self.theme["bg"])
        right_frame.pack(side="right", fill="y")
        
        self._create_options_section(right_frame)
        self._create_action_buttons(right_frame)

        # Main visualization area
        viz_frame = tk.Frame(self, bg=self.theme["bg"])
        viz_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(16, 10))
        self.fig.patch.set_facecolor(self.theme["bg"])
        self.ax.set_facecolor(self.theme["bg"])

        self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        toolbar = NavigationToolbar2Tk(self.canvas, viz_frame)
        toolbar.config(background=self.theme["panel"])
        toolbar._message_label.config(background=self.theme["panel"], 
                                      foreground=self.theme["text"])
        toolbar.update()

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self, textvariable=self.status_var,
                            bg=self.theme["panel"], fg=self.theme["text"],
                            anchor="w", padx=10)
        status_bar.pack(fill="x", side="bottom")

    def _create_input_section(self, parent):
        input_frame = tk.LabelFrame(parent, text="Configuration", 
                                   bg=self.theme["bg"], fg=self.theme["text"],
                                   font=("Arial", 10, "bold"))
        input_frame.pack(fill="x", padx=5, pady=5)

        # Maps
        tk.Label(input_frame, text="Maps (space-separated):", 
                fg=self.theme["text"], bg=self.theme["bg"]).grid(
                    row=0, column=0, sticky="w", padx=5, pady=3)
        self.maps_entry = tk.Entry(input_frame, bg=self.theme["panel"], 
                                  fg="white", width=40, font=("Consolas", 10))
        self.maps_entry.insert(0, "3x+1 5x+1 7x+1")
        self.maps_entry.grid(row=0, column=1, padx=5, pady=3, sticky="ew")

        # Starts
        tk.Label(input_frame, text="Start values (space-separated):", 
                fg=self.theme["text"], bg=self.theme["bg"]).grid(
                    row=1, column=0, sticky="w", padx=5, pady=3)
        self.starts_entry = tk.Entry(input_frame, bg=self.theme["panel"],
                                     fg="white", width=40, font=("Consolas", 10))
        self.starts_entry.insert(0, "7 15 27")
        self.starts_entry.grid(row=1, column=1, padx=5, pady=3, sticky="ew")

        # Range mode
        range_frame = tk.Frame(input_frame, bg=self.theme["bg"])
        range_frame.grid(row=2, column=1, sticky="w", padx=5, pady=3)
        
        tk.Label(range_frame, text="Or use range:", 
                fg=self.theme["text"], bg=self.theme["bg"]).pack(side="left")
        self.range_start = tk.Entry(range_frame, bg=self.theme["panel"],
                                   fg="white", width=8)
        self.range_start.pack(side="left", padx=2)
        tk.Label(range_frame, text="to", fg=self.theme["text"],
                bg=self.theme["bg"]).pack(side="left")
        self.range_end = tk.Entry(range_frame, bg=self.theme["panel"],
                                 fg="white", width=8)
        self.range_end.pack(side="left", padx=2)

        # Advanced Config Button
        tk.Button(
            input_frame,
            text="⚙️ Advanced Config",
            command=self.open_advanced_config,
            bg=self.theme["highlight"],
            fg="white",
            font=("Arial", 9, "bold")
        ).grid(row=3, column=1, sticky="w", padx=5, pady=3)

        # Max steps
        tk.Label(input_frame, text="Max steps:", fg=self.theme["text"],
                bg=self.theme["bg"]).grid(row=4, column=0, sticky="w", 
                                         padx=5, pady=3)
        self.steps_entry = tk.Entry(input_frame, bg=self.theme["panel"],
                                    fg="white", width=12)
        self.steps_entry.insert(0, "500")
        self.steps_entry.grid(row=4, column=1, sticky="w", padx=5, pady=3)

        input_frame.columnconfigure(1, weight=1)

    def _create_options_section(self, parent):
        options_frame = tk.LabelFrame(parent, text="Visualization Options",
                                     bg=self.theme["bg"], fg=self.theme["text"],
                                     font=("Arial", 10, "bold"))
        options_frame.pack(fill="x", padx=5, pady=5)

        # Fixed: Proper checkbutton for animation
        tk.Checkbutton(
            options_frame, 
            text="Animate", 
            variable=self.animate_var,
            bg=self.theme["bg"], 
            fg=self.theme["text"],
            selectcolor=self.theme["bg"]
        ).pack(anchor="w", padx=5)

        tk.Checkbutton(options_frame, text="Show labels", 
                      variable=self.show_labels, command=self.redraw,
                      bg=self.theme["bg"], fg=self.theme["text"],
                      selectcolor=self.theme["bg"]).pack(anchor="w", padx=5)

        tk.Checkbutton(options_frame, text="Show grid", 
                      variable=self.show_grid, command=self.redraw,
                      bg=self.theme["bg"], fg=self.theme["text"],
                      selectcolor=self.theme["bg"]).pack(anchor="w", padx=5)

        tk.Checkbutton(options_frame, text="Log scale", 
                      variable=self.log_scale, command=self.redraw,
                      bg=self.theme["bg"], fg=self.theme["text"],
                      selectcolor=self.theme["bg"]).pack(anchor="w", padx=5)

        tk.Checkbutton(options_frame, text="Show peaks", 
                      variable=self.show_peaks, command=self.redraw,
                      bg=self.theme["bg"], fg=self.theme["text"],
                      selectcolor=self.theme["bg"]).pack(anchor="w", padx=5)

    def _create_action_buttons(self, parent):
        button_frame = tk.Frame(parent, bg=self.theme["bg"])
        button_frame.pack(fill="x", padx=5, pady=10)

        btn_style = {"bg": self.theme["accent"], "fg": "white", 
                    "font": ("Arial", 10, "bold"), "width": 15}

        tk.Button(button_frame, text="🚀 Visualize", command=self.visualize,
                 **btn_style).pack(pady=3)
        
        tk.Button(button_frame, text="📊 Deep Analysis", 
                 command=self.show_analysis, bg=self.theme["highlight"],
                 fg="white", font=("Arial", 10, "bold"), width=15
                 ).pack(pady=3)
        
        tk.Button(button_frame, text="📈 Statistics", 
                 command=self.show_statistics,
                 **btn_style).pack(pady=3)
        
        tk.Button(button_frame, text="💾 Export PNG", 
                 command=self.export_png,
                 **btn_style).pack(pady=3)
        
        tk.Button(button_frame, text="📋 Export Data", 
                 command=self.export_data,
                 **btn_style).pack(pady=3)

    # --------------------------------------------------
    # Core Functionality
    # --------------------------------------------------

    def open_advanced_config(self):
        """Open advanced configuration modal"""
        modal = AdvancedConfigModal(self)
        self.wait_window(modal)
        
        if modal.result:
            self.advanced_config = modal.result
            self.status_var.set(f"Advanced config loaded: {len(modal.result)} map-start combinations")
        else:
            self.advanced_config = None

    def get_start_values(self):
        """Get start values from entry or range"""
        if self.range_start.get() and self.range_end.get():
            start = int(self.range_start.get())
            end = int(self.range_end.get())
            return list(range(start, end + 1))
        else:
            return [int(x) for x in self.starts_entry.get().split()]

    def visualize(self):
        """Main visualization routine"""
        try:
            if self.animation is not None:
                if self.animation.event_source is not None:
                    self.animation.event_source.stop()
                self.animation = None

            self.status_var.set("Computing orbits...")
            self.update()

            max_steps = int(self.steps_entry.get())
            self.results.clear()
            self.analyses.clear()
            cmap = plt.get_cmap("tab20")

            total_computed = 0
            
            # Use advanced config if available
            if self.advanced_config:
                for i, (map_tuple, starts) in enumerate(self.advanced_config):
                    color = cmap(i % 20)
                    for s in starts:
                        seq, cycle, cycled = collatz_orbit(s, *map_tuple, max_steps)
                        self.results[map_tuple].append((s, seq, cycle, cycled, color))
                        
                        # Perform analysis
                        analysis = analyze_sequence(seq, cycle, cycled)
                        self.analyses[map_tuple].append((s, analysis))
                        
                        total_computed += 1
                        if total_computed % 10 == 0:
                            self.status_var.set(f"Computed {total_computed} orbits...")
                            self.update()
            else:
                # Use standard config
                maps = [parse_map(m) for m in self.maps_entry.get().split()]
                starts = self.get_start_values()
                
                for i, m in enumerate(maps):
                    color = cmap(i % 20)
                    for j, s in enumerate(starts):
                        seq, cycle, cycled = collatz_orbit(s, *m, max_steps)
                        self.results[m].append((s, seq, cycle, cycled, color))
                        
                        # Perform analysis
                        analysis = analyze_sequence(seq, cycle, cycled)
                        self.analyses[m].append((s, analysis))
                        
                        total_computed += 1
                        if total_computed % 10 == 0:
                            self.status_var.set(f"Computed {total_computed} orbits...")
                            self.update()

            self.status_var.set(f"Rendering {total_computed} orbits...")
            self.update()

            # Fixed: Use .get() to check BooleanVar
            if self.animate_var.get():
                self.animate()
            else:
                self.draw_static()

            self.status_var.set(f"✓ Visualized {total_computed} orbits")

        except Exception as e:
            messagebox.showerror("Error", f"Visualization failed: {str(e)}")
            self.status_var.set("Error occurred")

    def compute_visual_scale(self):
        """Adaptive scaling based on data density"""
        total_points = sum(
            len(seq) for seqs in self.results.values()
            for _, seq, _, _, _ in seqs
        )
        if total_points <= 0:
            return 1.0
        scale = (REF_POINTS / total_points) ** 0.5
        return float(max(0.3, min(3.0, scale)))

    def draw_static(self):
        """Render static visualization"""
        self.ax.clear()
        
        if self.log_scale.get():
            self.ax.set_yscale("log")
        
        if self.show_grid.get():
            self.ax.grid(True, alpha=0.2, color=self.theme["text"])

        scale = self.compute_visual_scale()
        node_size = max(NODE_MIN, min(NODE_MAX, 60 * scale))
        glow_size = max(GLOW_MIN, min(GLOW_MAX, 900 * scale))
        label_size = max(LABEL_MIN, min(LABEL_MAX, 9 * scale))

        for map_key, seqs in self.results.items():
            for start, seq, cycle, cycled, color in seqs:
                xs = list(range(len(seq)))
                
                # Convert to float for plotting if values are reasonable
                plot_seq = seq
                if max(seq) < 1e15:  # Safe for float conversion
                    plot_seq = [float(x) for x in seq]
                
                # Main trajectory
                self.ax.plot(xs, plot_seq, color=color, alpha=0.7, linewidth=1.5,
                           label=f"{map_key[0]}x{map_key[1]:+d} @ {start}" 
                           if len(seqs) == 1 else None)
                
                self.ax.scatter(xs, plot_seq, s=node_size, color=color, 
                              alpha=0.8, edgecolors='white', linewidth=0.5)

                # Cycle highlighting
                if cycled:
                    cycle_x = list(range(len(seq) - len(cycle), len(seq)))
                    plot_cycle = cycle if max(cycle) < 1e15 else [float(x) for x in cycle]
                    self.ax.scatter(cycle_x, plot_cycle, s=glow_size,
                                  color=color, alpha=0.15, marker='o')
                    # Add cycle border
                    self.ax.plot(cycle_x, plot_cycle, color=color, linewidth=3,
                               alpha=0.4, linestyle='--')

                # Peak markers
                if self.show_peaks.get():
                    for i in range(1, len(seq) - 1):
                        if seq[i] > seq[i-1] and seq[i] > seq[i+1]:
                            plot_val = float(seq[i]) if seq[i] < 1e15 else seq[i]
                            self.ax.scatter([i], [plot_val], s=node_size*2,
                                          marker='^', color='yellow',
                                          edgecolors='red', linewidth=2,
                                          zorder=10)

                # Labels
                if self.show_labels.get():
                    self.draw_labels(xs, plot_seq, label_size)

        self.ax.set_xlabel("Step", color=self.theme["text"], fontsize=12)
        self.ax.set_ylabel("Value", color=self.theme["text"], fontsize=12)
        self.ax.set_title("Collatz Orbital Trajectories", 
                         color=self.theme["text"], fontsize=16, 
                         fontweight='bold', pad=20)
        self.ax.tick_params(colors=self.theme["text"])
        
        if len(self.results) <= 5:
            self.ax.legend(facecolor=self.theme["panel"], 
                          edgecolor=self.theme["text"],
                          labelcolor=self.theme["text"])

        self.canvas.draw_idle()

    def draw_labels(self, xs, ys, fontsize):
        """Draw value labels on points"""
        step = max(1, len(xs) // 20)  # Limit label density
        for i, (x, y) in enumerate(zip(xs, ys)):
            if i % step == 0 and y < 99999:
                self.ax.text(x, y, str(int(y)) if isinstance(y, float) else str(y), 
                           fontsize=fontsize,
                           color=self.theme["text"], ha="center",
                           va="bottom", alpha=0.7)

    def animate(self):
        """Animated visualization"""
        self.ax.clear()
        
        max_len = max(
            len(seq) for seqs in self.results.values()
            for _, seq, _, _, _ in seqs
        )

        def update(frame):
            self.ax.clear()
            if self.log_scale.get():
                self.ax.set_yscale("log")
            if self.show_grid.get():
                self.ax.grid(True, alpha=0.2, color=self.theme["text"])

            scale = self.compute_visual_scale()
            node_size = max(NODE_MIN, min(NODE_MAX, 60 * scale))
            glow_size = max(GLOW_MIN, min(GLOW_MAX, 900 * scale))
            label_size = max(LABEL_MIN, min(LABEL_MAX, 9 * scale))

            for seqs in self.results.values():
                for _, seq, cycle, cycled, color in seqs:
                    if not seq:  # Skip empty sequences
                        continue
                        
                    f = min(frame, len(seq))
                    if f == 0:  # Skip if frame is before sequence starts
                        continue
                        
                    xs = list(range(f))
                    ys = seq[:f]
                    
                    if not ys:  # Double check ys is not empty
                        continue
                    
                    # Convert for plotting
                    plot_ys = ys if max(ys) < 1e15 else [float(x) for x in ys]

                    self.ax.plot(xs, plot_ys, color=color, alpha=0.7, linewidth=1.5)
                    self.ax.scatter(xs, plot_ys, s=node_size, color=color, alpha=0.8)

                    if cycled and f >= len(seq) and cycle:
                        cycle_x = list(range(len(seq) - len(cycle), len(seq)))
                        plot_cycle = cycle if max(cycle) < 1e15 else [float(x) for x in cycle]
                        self.ax.scatter(cycle_x, plot_cycle, s=glow_size,
                                      color=color, alpha=0.15)

                    if self.show_labels.get() and plot_ys:
                        self.draw_labels(xs, plot_ys, label_size)

            self.ax.set_title(f"Collatz Trajectories - Step {frame}/{max_len}",
                            color=self.theme["text"], fontsize=16)
            self.ax.tick_params(colors=self.theme["text"])
            self.ax.set_xlabel("Step", color=self.theme["text"], fontsize=12)
            self.ax.set_ylabel("Value", color=self.theme["text"], fontsize=12)

        self.animation = FuncAnimation(self.fig, update,
                                      frames=max_len + 5,
                                      interval=30, repeat=False)
        self.canvas.draw_idle()

    def redraw(self):
        """Redraw without recomputing"""
        if not self.animate_var.get() and self.results:
            self.draw_static()

    # --------------------------------------------------
    # Analysis Windows
    # --------------------------------------------------

    def show_analysis(self):
        """Show detailed analysis window"""
        if not self.results:
            messagebox.showinfo("Analysis", "Run a visualization first.")
            return

        win = tk.Toplevel(self)
        win.title("Deep Collatz Analysis")
        win.configure(bg=self.theme["bg"])
        win.geometry("1200x800")

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        for m, analyses in self.analyses.items():
            tab = tk.Frame(notebook, bg=self.theme["bg"])
            notebook.add(tab, text=f"Map: {m[0]}x{m[1]:+d}")

            # Treeview for detailed data
            tree_frame = tk.Frame(tab, bg=self.theme["bg"])
            tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

            tree = ttk.Treeview(
                tree_frame,
                columns=("start", "length", "max", "mean", "trajectory", 
                        "cycle", "peaks", "even_ratio"),
                show="headings"
            )

            headers = {
                "start": "Start",
                "length": "Steps",
                "max": "Max Value",
                "mean": "Mean",
                "trajectory": "Outcome",
                "cycle": "Cycle Length",
                "peaks": "Peaks",
                "even_ratio": "Even %"
            }

            for col, header in headers.items():
                tree.heading(col, text=header)
                tree.column(col, width=100)

            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical",
                                     command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            tree.pack(fill="both", expand=True)

            for start, analysis in analyses:
                even_ratio = (analysis["even_count"] / analysis["length"] * 100
                            if analysis["length"] > 0 else 0)
                
                # Format large numbers
                max_val = analysis['max_value']
                if max_val > 1e12:
                    max_str = f"{max_val:.2e}"
                else:
                    max_str = f"{max_val:,}"
                
                tree.insert("", "end", values=(
                    start,
                    analysis["length"],
                    max_str,
                    f"{analysis['mean']:.1f}",
                    analysis["trajectory"],
                    analysis["cycle_length"],
                    analysis["peak_count"],
                    f"{even_ratio:.1f}%"
                ))

            # Summary section
            summary_frame = tk.Frame(tab, bg=self.theme["panel"])
            summary_frame.pack(fill="x", padx=10, pady=5)

            summary_text = self._generate_summary(analyses)
            summary_label = tk.Label(summary_frame, text=summary_text,
                                    bg=self.theme["panel"],
                                    fg=self.theme["text"],
                                    justify="left", font=("Consolas", 10))
            summary_label.pack(padx=10, pady=10)

    def _generate_summary(self, analyses):
        """Generate statistical summary"""
        if not analyses:
            return "No data"

        trajectories = Counter(a["trajectory"] for _, a in analyses)
        lengths = [a["length"] for _, a in analyses]
        max_vals = [a["max_value"] for _, a in analyses]

        # Format largest value
        largest = max(max_vals)
        if largest > 1e12:
            largest_str = f"{largest:.2e}"
        else:
            largest_str = f"{largest:,}"

        summary = f"""
╔═══════════════════════════════════════════════╗
║          STATISTICAL SUMMARY                  ║
╠═══════════════════════════════════════════════╣
║ Total Orbits: {len(analyses):<30} ║
║ Cyclic: {trajectories.get('Cyclic', 0):<36} ║
║ Divergent: {trajectories.get('Divergent/Runaway', 0):<33} ║
║ Terminated: {trajectories.get('Terminated', 0):<32} ║
║ Collapsed: {trajectories.get('Collapsed', 0):<33} ║
╠═══════════════════════════════════════════════╣
║ Avg Steps: {safe_mean(lengths):.1f}{' '*(33-len(f'{safe_mean(lengths):.1f}'))}║
║ Max Steps: {max(lengths):<33} ║
║ Largest Value Reached: {largest_str}{' '*(20-len(largest_str))}║
╚═══════════════════════════════════════════════╝
        """
        return summary

    def show_statistics(self):
        """Show comprehensive statistics window"""
        if not self.analyses:
            messagebox.showinfo("Statistics", "Run a visualization first.")
            return

        win = tk.Toplevel(self)
        win.title("Comprehensive Statistics")
        win.configure(bg=self.theme["bg"])
        win.geometry("900x700")

        text = scrolledtext.ScrolledText(win, bg=self.theme["panel"],
                                        fg=self.theme["text"],
                                        font=("Consolas", 10))
        text.pack(fill="both", expand=True, padx=10, pady=10)

        stats = self._compute_comprehensive_stats()
        text.insert("1.0", stats)
        text.config(state="disabled")

    def _compute_comprehensive_stats(self):
        """Compute comprehensive statistics across all maps"""
        output = []
        output.append("=" * 70)
        output.append(" " * 15 + "COMPREHENSIVE COLLATZ ANALYSIS")
        output.append("=" * 70)
        output.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for map_key, analyses in self.analyses.items():
            output.append(f"\n{'─' * 70}")
            output.append(f"Map: {map_key[0]}x{map_key[1]:+d}")
            output.append(f"{'─' * 70}\n")

            lengths = [a["length"] for _, a in analyses]
            max_vals = [a["max_value"] for _, a in analyses]
            means = [a["mean"] for _, a in analyses]
            peaks = [a["peak_count"] for _, a in analyses]

            output.append(f"Number of orbits computed: {len(analyses)}")
            output.append(f"\nStep Statistics:")
            output.append(f"  Mean: {safe_mean(lengths):.2f}")
            output.append(f"  Median: {safe_median(lengths):.2f}")
            output.append(f"  Std Dev: {safe_std(lengths):.2f}")
            output.append(f"  Min: {min(lengths)}")
            output.append(f"  Max: {max(lengths)}")

            # Format largest value
            largest = max(max_vals)
            if largest > 1e12:
                largest_str = f"{largest:.2e}"
            else:
                largest_str = f"{largest:,}"

            output.append(f"\nValue Statistics:")
            output.append(f"  Largest value reached: {largest_str}")
            output.append(f"  Average maximum: {safe_mean(max_vals):.2f}")
            output.append(f"  Average mean: {safe_mean(means):.2f}")

            output.append(f"\nTrajectory Distribution:")
            trajectories = Counter(a["trajectory"] for _, a in analyses)
            for traj, count in trajectories.items():
                percentage = (count / len(analyses)) * 100
                output.append(f"  {traj}: {count} ({percentage:.1f}%)")

            output.append(f"\nPeak Statistics:")
            output.append(f"  Average peaks per orbit: {safe_mean(peaks):.2f}")
            output.append(f"  Max peaks in single orbit: {max(peaks)}")

            # Cycle analysis
            cyclic = [(s, a) for s, a in analyses if a["cycled"]]
            if cyclic:
                output.append(f"\nCycle Analysis:")
                output.append(f"  Cyclic orbits: {len(cyclic)}")
                cycle_lengths = [a["cycle_length"] for _, a in cyclic]
                output.append(f"  Average cycle length: {safe_mean(cycle_lengths):.2f}")
                output.append(f"  Cycle length range: {min(cycle_lengths)} - {max(cycle_lengths)}")

        output.append(f"\n{'=' * 70}\n")
        return "\n".join(output)

    # --------------------------------------------------
    # Export Functions
    # --------------------------------------------------

    def export_png(self):
        """Export current visualization as PNG"""
        if not self.results:
            messagebox.showinfo("Export", "Nothing to export. Visualize first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if path:
            self.fig.savefig(path, dpi=300, facecolor=self.fig.get_facecolor(),
                           bbox_inches='tight')
            messagebox.showinfo("Success", f"Exported to {path}")
            self.status_var.set(f"Exported to {path}")

    def export_data(self):
        """Export analysis data as JSON"""
        if not self.analyses:
            messagebox.showinfo("Export", "No data to export. Run analysis first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            export_data = {}
            for map_key, analyses in self.analyses.items():
                map_str = f"{map_key[0]}x{map_key[1]:+d}"
                export_data[map_str] = []
                
                for start, analysis in analyses:
                    # Convert all values to JSON-serializable types
                    analysis_copy = {}
                    for key, value in analysis.items():
                        if isinstance(value, (int, float, str, bool, type(None))):
                            analysis_copy[key] = value
                        else:
                            analysis_copy[key] = str(value)
                    
                    export_data[map_str].append({
                        "start_value": start,
                        "analysis": analysis_copy
                    })

            with open(path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Data exported to {path}")
            self.status_var.set(f"Data exported to {path}")


# ======================================================
# Launch Application
# ======================================================

if __name__ == "__main__":
    app = CollatzVisualizer()
    app.mainloop()
