from __future__ import annotations

import csv
from collections import defaultdict, deque
import ctypes
import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .gpu_tracer import sample_gpu_engine_running_times, sample_gpu_engines, trace_gpu_processes
from .opencl_probe import probe_opencl
from .power import build_counter_paths, collect_power_sample
from .uma import inspect_uma


class AmdApuGui:
    def __init__(self, refresh: float, record_path: Path) -> None:
        self.refresh_ms = max(250, int(refresh * 1000))
        self.record_path = record_path
        self.settings_path = record_path.parent / "gui_settings.json"
        self.counter_paths = build_counter_paths()
        self.opencl_result = probe_opencl(iterations=1)
        self._enable_dpi_awareness()
        self.history = {
            "labels": deque(maxlen=40),
            "cpu": deque(maxlen=40),
            "gpu": deque(maxlen=40),
            "ram": deque(maxlen=40),
            "shared": deque(maxlen=40),
            "dedicated": deque(maxlen=40),
            "engine_3d": deque(maxlen=40),
            "engine_compute": deque(maxlen=40),
            "engine_copy": deque(maxlen=40),
            "engine_video": deque(maxlen=40),
        }
        self.recording = False
        self.record_file = None
        self.record_writer = None
        self.gpu_focus_samples: deque[dict[str, object]] = deque(maxlen=240)
        self.process_history: dict[int, deque[float]] = defaultdict(lambda: deque(maxlen=20))
        self.last_engine_running_times: dict[str, float] = {}
        self.last_sample: dict[str, float | str | None] | None = None
        self.last_pressure_score = 0
        self.thresholds = self._load_thresholds()

        self.root = tk.Tk()
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.tk_scaling = float(self.root.tk.call("tk", "scaling"))
        self.compact_mode = self.screen_width <= 1366 or self.screen_height <= 768
        self.ui_scale = min(1.25, max(0.95, self.tk_scaling / 1.33))
        self.chart_dpi = int(120 if self.compact_mode else 140)
        self.root.title("AMD APU Monitor")
        width = min(max(1100, self.screen_width - 32), 1520)
        height = min(max(680, self.screen_height - 80), 980)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(1024, 640)
        self.root.configure(bg="#0d1117")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.status_var = tk.StringVar(value="Initializing...")
        self.record_var = tk.StringVar(value="Recording: Off")
        self.alert_var = tk.StringVar(value="No active alerts.")
        self.active_view = tk.StringVar(value="gpu_focus")
        self.threshold_vars = {
            "moderate_pressure_score": tk.StringVar(value=str(self.thresholds["moderate_pressure_score"])),
            "high_pressure_score": tk.StringVar(value=str(self.thresholds["high_pressure_score"])),
            "gpu_util_alert": tk.StringVar(value=str(self.thresholds["gpu_util_alert"])),
            "free_ram_alert_gb": tk.StringVar(value=str(self.thresholds["free_ram_alert_gb"])),
        }
        self.value_vars = {
            "verdict": tk.StringVar(value="n/a"),
            "pressure": tk.StringVar(value="n/a"),
            "cpu": tk.StringVar(value="n/a"),
            "gpu": tk.StringVar(value="n/a"),
            "ram": tk.StringVar(value="n/a"),
            "shared": tk.StringVar(value="n/a"),
            "dedicated": tk.StringVar(value="n/a"),
            "committed": tk.StringVar(value="n/a"),
            "top_engine": tk.StringVar(value="n/a"),
            "active_gpu_procs": tk.StringVar(value="n/a"),
            "gpu_alerts": tk.StringVar(value="No GPU spikes."),
            "selected_proc": tk.StringVar(value="Select a GPU process"),
            "selected_proc_history": tk.StringVar(value="Recent GPU%: n/a"),
            "engine_runtime": tk.StringVar(value="Runtime delta: n/a"),
            "opencl_device": tk.StringVar(value=str(self.opencl_result.device_name)),
            "opencl_version": tk.StringVar(value=str(self.opencl_result.platform_version)),
            "opencl_units": tk.StringVar(value=str(self.opencl_result.max_compute_units)),
            "opencl_unified": tk.StringVar(value=str(self.opencl_result.unified_memory)),
            "opencl_clinfo": tk.StringVar(value=f"{self.opencl_result.average_clinfo_ms:.2f} ms"),
        }

        self._build_ui()

    def _enable_dpi_awareness(self) -> None:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    def _build_ui(self) -> None:
        title_size = round((16 if self.compact_mode else 22) * self.ui_scale)
        status_size = round((8 if self.compact_mode else 10) * self.ui_scale)
        body_size = round((8 if self.compact_mode else 10) * self.ui_scale)
        metric_size = round((12 if self.compact_mode else 18) * self.ui_scale)
        nav_size = round((9 if self.compact_mode else 11) * self.ui_scale)
        button_pad_x = 4 if self.compact_mode else 6
        button_pad_y = 2 if self.compact_mode else 4
        outer_pad = 8 if self.compact_mode else 16
        section_pad = 6 if self.compact_mode else 12

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Root.TFrame", background="#0d1117")
        style.configure("Card.TLabelframe", background="#161b22", foreground="#dbe6f3", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background="#161b22", foreground="#8bbee8")
        style.configure("MetricLabel.TLabel", background="#161b22", foreground="#8fa3b8", font=("Segoe UI", body_size))
        style.configure("MetricValue.TLabel", background="#161b22", foreground="#f4f7fa", font=("Segoe UI Semibold", metric_size))
        style.configure("Status.TLabel", background="#0d1117", foreground="#dbe6f3", font=("Segoe UI", status_size))
        style.configure("Body.TLabel", background="#161b22", foreground="#dbe6f3", font=("Segoe UI", body_size))
        style.configure("Alert.TLabel", background="#28161a", foreground="#ffccd5", font=("Segoe UI", body_size + 1))
        style.configure("Nav.TButton", font=("Segoe UI Semibold", nav_size))

        root_frame = ttk.Frame(self.root, style="Root.TFrame", padding=outer_pad)
        root_frame.pack(fill="both", expand=True)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(2, weight=1)

        header = ttk.Frame(root_frame, style="Root.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, section_pad))
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="AMD APU Desktop Monitor",
            font=("Segoe UI Semibold", title_size),
            foreground="#f4f7fa",
            background="#0d1117",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.status_var, style="Status.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 0))

        controls = ttk.Frame(header, style="Root.TFrame")
        controls.grid(row=0, column=1, rowspan=2, sticky="ne")
        ttk.Button(controls, text="Record CSV", command=self._toggle_recording).grid(row=0, column=0, padx=(0, button_pad_x), pady=(0, button_pad_y))
        ttk.Button(controls, text="Export Chart", command=self._export_chart).grid(row=0, column=1, padx=(0, button_pad_x), pady=(0, button_pad_y))
        ttk.Button(controls, text="Refresh Now", command=self._refresh_once).grid(row=0, column=2, pady=(0, button_pad_y))
        ttk.Label(controls, textvariable=self.record_var, style="Status.TLabel").grid(row=1, column=0, columnspan=3, sticky="e")

        nav = ttk.Frame(root_frame, style="Root.TFrame")
        nav.grid(row=1, column=0, sticky="ew", pady=(0, section_pad))
        ttk.Button(nav, text="GPU Focus", style="Nav.TButton", command=lambda: self._show_view("gpu_focus")).grid(row=0, column=0, padx=(0, button_pad_x))
        ttk.Button(nav, text="GPU / CPU", style="Nav.TButton", command=lambda: self._show_view("gpu_cpu")).grid(row=0, column=1, padx=(0, button_pad_x))
        ttk.Button(nav, text="RAM", style="Nav.TButton", command=lambda: self._show_view("ram")).grid(row=0, column=2, padx=(0, button_pad_x))
        ttk.Button(nav, text="Overview", style="Nav.TButton", command=lambda: self._show_view("overview")).grid(row=0, column=3)

        self.content = ttk.Frame(root_frame, style="Root.TFrame")
        self.content.grid(row=2, column=0, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

        self.views: dict[str, ttk.Frame] = {}
        self._build_gpu_focus_view()
        self._build_gpu_cpu_view()
        self._build_ram_view()
        self._build_overview_view()
        self._show_view("gpu_focus")

    def _build_gpu_focus_view(self) -> None:
        frame = ttk.Frame(self.content, style="Root.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(1, weight=1)

        cards = ttk.Frame(frame, style="Root.TFrame")
        cards.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8 if self.compact_mode else 12))
        for index in range(4):
            cards.columnconfigure(index, weight=1)
        self._metric_card(cards, "GPU Util", self.value_vars["gpu"], 0, 0)
        self._metric_card(cards, "Top Engine", self.value_vars["top_engine"], 0, 1)
        self._metric_card(cards, "GPU Shared", self.value_vars["shared"], 0, 2)
        self._metric_card(cards, "Active GPU Procs", self.value_vars["active_gpu_procs"], 0, 3)

        chart_card = ttk.LabelFrame(frame, text="GPU Engine Activity", style="Card.TLabelframe", padding=4 if self.compact_mode else 10)
        chart_card.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        chart_card.rowconfigure(0, weight=1)
        chart_card.columnconfigure(0, weight=1)
        self.gpu_focus_figure = Figure(figsize=(9.8, 6.2) if self.compact_mode else (11.5, 7.8), dpi=self.chart_dpi, facecolor="#161b22")
        self.gpu_focus_ax = self.gpu_focus_figure.add_subplot(111)
        self._style_axis(self.gpu_focus_ax)
        self.gpu_focus_canvas = FigureCanvasTkAgg(self.gpu_focus_figure, master=chart_card)
        self.gpu_focus_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        side = ttk.Frame(frame, style="Root.TFrame")
        side.grid(row=1, column=1, sticky="nsew")
        side.rowconfigure(1, weight=1)
        side.columnconfigure(0, weight=1)

        gpu_mem_frame = ttk.LabelFrame(side, text="GPU Memory", style="Card.TLabelframe", padding=12)
        gpu_mem_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        self._detail_row(gpu_mem_frame, "Shared", self.value_vars["shared"], 0)
        self._detail_row(gpu_mem_frame, "Dedicated", self.value_vars["dedicated"], 1)
        self._detail_row(gpu_mem_frame, "Committed", self.value_vars["committed"], 2)
        self._detail_row(gpu_mem_frame, "Runtime Delta", self.value_vars["engine_runtime"], 3)

        proc_frame = ttk.LabelFrame(side, text="Top GPU Processes", style="Card.TLabelframe", padding=10)
        proc_frame.grid(row=1, column=0, sticky="nsew")
        proc_frame.rowconfigure(0, weight=1)
        proc_frame.columnconfigure(0, weight=1)
        columns = ("gpu", "pid", "name", "engines")
        self.gpu_focus_tree = ttk.Treeview(proc_frame, columns=columns, show="headings", height=10 if self.compact_mode else 14)
        for column, title, width in [
            ("gpu", "GPU %", 76),
            ("pid", "PID", 70),
            ("name", "Process", 120),
            ("engines", "Active Engines", 240 if self.compact_mode else 280),
        ]:
            self.gpu_focus_tree.heading(column, text=title)
            self.gpu_focus_tree.column(column, width=width, anchor="w" if column in {"name", "engines"} else "center")
        self.gpu_focus_tree.grid(row=0, column=0, sticky="nsew")
        self.gpu_focus_tree.bind("<<TreeviewSelect>>", self._on_gpu_focus_select)
        focus_scroll = ttk.Scrollbar(proc_frame, orient="vertical", command=self.gpu_focus_tree.yview)
        focus_scroll.grid(row=0, column=1, sticky="ns")
        self.gpu_focus_tree.configure(yscrollcommand=focus_scroll.set)

        detail_frame = ttk.LabelFrame(side, text="GPU Alerts + Process Detail", style="Card.TLabelframe", padding=12)
        detail_frame.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(detail_frame, textvariable=self.value_vars["gpu_alerts"], style="Alert.TLabel", wraplength=300 if self.compact_mode else 360, justify="left").pack(fill="x", pady=(0, 8))
        ttk.Label(detail_frame, textvariable=self.value_vars["selected_proc"], style="Body.TLabel", wraplength=320 if self.compact_mode else 380, justify="left").pack(fill="x")
        ttk.Label(detail_frame, textvariable=self.value_vars["selected_proc_history"], style="Body.TLabel", wraplength=320 if self.compact_mode else 380, justify="left").pack(fill="x", pady=(6, 0))
        mini_chart_host = ttk.Frame(detail_frame, style="Root.TFrame")
        mini_chart_host.pack(fill="both", expand=True, pady=(8, 0))
        self.proc_mini_figure = Figure(figsize=(3.6, 1.6), dpi=self.chart_dpi, facecolor="#161b22")
        self.proc_mini_ax = self.proc_mini_figure.add_subplot(111)
        self._style_axis(self.proc_mini_ax)
        self.proc_mini_canvas = FigureCanvasTkAgg(self.proc_mini_figure, master=mini_chart_host)
        self.proc_mini_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.views["gpu_focus"] = frame

    def _build_gpu_cpu_view(self) -> None:
        frame = ttk.Frame(self.content, style="Root.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        chart_card = ttk.LabelFrame(frame, text="GPU / CPU Utilization", style="Card.TLabelframe", padding=4 if self.compact_mode else 10)
        chart_card.grid(row=0, column=0, sticky="nsew")
        chart_card.rowconfigure(0, weight=1)
        chart_card.columnconfigure(0, weight=1)

        self.gpu_cpu_figure = Figure(figsize=(10.4, 6.1) if self.compact_mode else (13.5, 8.0), dpi=self.chart_dpi, facecolor="#161b22")
        self.gpu_cpu_ax = self.gpu_cpu_figure.add_subplot(111)
        self._style_axis(self.gpu_cpu_ax)
        self.gpu_cpu_canvas = FigureCanvasTkAgg(self.gpu_cpu_figure, master=chart_card)
        self.gpu_cpu_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.views["gpu_cpu"] = frame

    def _build_ram_view(self) -> None:
        frame = ttk.Frame(self.content, style="Root.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        chart_card = ttk.LabelFrame(frame, text="RAM + Shared GPU Memory", style="Card.TLabelframe", padding=4 if self.compact_mode else 10)
        chart_card.grid(row=0, column=0, sticky="nsew")
        chart_card.rowconfigure(0, weight=1)
        chart_card.columnconfigure(0, weight=1)

        self.ram_figure = Figure(figsize=(10.4, 6.1) if self.compact_mode else (13.5, 8.0), dpi=self.chart_dpi, facecolor="#161b22")
        self.ram_ax = self.ram_figure.add_subplot(111)
        self.ram_ax_right = self.ram_ax.twinx()
        self._style_axis(self.ram_ax)
        self._style_axis(self.ram_ax_right)
        self.ram_canvas = FigureCanvasTkAgg(self.ram_figure, master=chart_card)
        self.ram_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.views["ram"] = frame

    def _build_overview_view(self) -> None:
        frame = ttk.Frame(self.content, style="Root.TFrame")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(1, weight=1)

        cards = ttk.Frame(frame, style="Root.TFrame")
        cards.grid(row=0, column=0, columnspan=2, sticky="ew")
        for index in range(3):
            cards.columnconfigure(index, weight=1)
        self._metric_card(cards, "UMA Verdict", self.value_vars["verdict"], 0, 0)
        self._metric_card(cards, "Pressure Score", self.value_vars["pressure"], 0, 1)
        self._metric_card(cards, "GPU Shared", self.value_vars["shared"], 0, 2)
        self._metric_card(cards, "CPU Util", self.value_vars["cpu"], 1, 0)
        self._metric_card(cards, "GPU Util", self.value_vars["gpu"], 1, 1)
        self._metric_card(cards, "Free RAM", self.value_vars["ram"], 1, 2)

        left = ttk.Frame(frame, style="Root.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(12, 0))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        alert_frame = ttk.LabelFrame(left, text="Alerts", style="Card.TLabelframe", padding=12)
        alert_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(alert_frame, textvariable=self.alert_var, style="Alert.TLabel", wraplength=760, justify="left").pack(fill="x")

        proc_frame = ttk.LabelFrame(left, text="Top GPU Processes", style="Card.TLabelframe", padding=10)
        proc_frame.grid(row=1, column=0, sticky="nsew")
        proc_frame.rowconfigure(0, weight=1)
        proc_frame.columnconfigure(0, weight=1)
        columns = ("gpu", "pid", "name", "engines")
        self.proc_tree = ttk.Treeview(proc_frame, columns=columns, show="headings", height=10 if self.compact_mode else 14)
        self.proc_tree.heading("gpu", text="GPU %")
        self.proc_tree.heading("pid", text="PID")
        self.proc_tree.heading("name", text="Process")
        self.proc_tree.heading("engines", text="Active Engines")
        self.proc_tree.column("gpu", width=80, anchor="e")
        self.proc_tree.column("pid", width=80, anchor="center")
        self.proc_tree.column("name", width=140, anchor="w")
        self.proc_tree.column("engines", width=220 if self.compact_mode else 320, anchor="w")
        self.proc_tree.grid(row=0, column=0, sticky="nsew")
        proc_scroll = ttk.Scrollbar(proc_frame, orient="vertical", command=self.proc_tree.yview)
        proc_scroll.grid(row=0, column=1, sticky="ns")
        self.proc_tree.configure(yscrollcommand=proc_scroll.set)

        right = ttk.Frame(frame, style="Root.TFrame")
        right.grid(row=1, column=1, sticky="nsew", pady=(12, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        opencl_frame = ttk.LabelFrame(right, text="OpenCL Runtime", style="Card.TLabelframe", padding=12)
        opencl_frame.grid(row=0, column=0, sticky="ew")
        self._detail_row(opencl_frame, "Device", self.value_vars["opencl_device"], 0)
        self._detail_row(opencl_frame, "Platform", self.value_vars["opencl_version"], 1)
        self._detail_row(opencl_frame, "Compute Units", self.value_vars["opencl_units"], 2)
        self._detail_row(opencl_frame, "Unified Memory", self.value_vars["opencl_unified"], 3)
        self._detail_row(opencl_frame, "clinfo Avg", self.value_vars["opencl_clinfo"], 4)

        settings_frame = ttk.LabelFrame(right, text="Alert Thresholds", style="Card.TLabelframe", padding=12)
        settings_frame.grid(row=1, column=0, sticky="ew", pady=(12, 12))
        self._settings_row(settings_frame, "Moderate Pressure", self.threshold_vars["moderate_pressure_score"], 0)
        self._settings_row(settings_frame, "High Pressure", self.threshold_vars["high_pressure_score"], 1)
        self._settings_row(settings_frame, "GPU Util Alert %", self.threshold_vars["gpu_util_alert"], 2)
        self._settings_row(settings_frame, "Free RAM Alert GB", self.threshold_vars["free_ram_alert_gb"], 3)
        ttk.Button(settings_frame, text="Apply Thresholds", command=self._apply_thresholds).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        help_frame = ttk.LabelFrame(right, text="Interpretation", style="Card.TLabelframe", padding=12)
        help_frame.grid(row=2, column=0, sticky="nsew")
        help_text = (
            "Use GPU / CPU for utilization spikes.\n\n"
            "Use RAM to watch memory headroom and shared iGPU pressure.\n\n"
            "Use Overview for alerts, top GPU processes, and runtime details."
        )
        ttk.Label(help_frame, text=help_text, style="Body.TLabel", wraplength=280 if self.compact_mode else 360, justify="left").pack(fill="both", expand=True)

        gpu_mem_frame = ttk.LabelFrame(right, text="GPU Memory", style="Card.TLabelframe", padding=12)
        gpu_mem_frame.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        self._detail_row(gpu_mem_frame, "Shared", self.value_vars["shared"], 0)
        self._detail_row(gpu_mem_frame, "Dedicated", self.value_vars["dedicated"], 1)
        self._detail_row(gpu_mem_frame, "Committed", self.value_vars["committed"], 2)

        self.views["overview"] = frame

    def _metric_card(self, parent, title: str, variable: tk.StringVar, row: int, column: int) -> None:
        card = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe", padding=12)
        card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        ttk.Label(card, textvariable=variable, style="MetricValue.TLabel").pack(anchor="w")

    def _detail_row(self, parent, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label, style="MetricLabel.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Label(parent, textvariable=variable, style="Body.TLabel", wraplength=220, justify="right").grid(row=row, column=1, sticky="e", pady=4)

    def _settings_row(self, parent, label: str, variable: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label, style="MetricLabel.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(parent, textvariable=variable, width=12).grid(row=row, column=1, sticky="e", pady=4)

    def _style_axis(self, axis) -> None:
        axis.set_facecolor("#161b22")
        axis.tick_params(colors="#b8c7d9", labelsize=8 if self.compact_mode else 11)
        for spine in axis.spines.values():
            spine.set_color("#425466")
        axis.grid(True, color="#27313d", alpha=0.7)
        axis.title.set_fontsize(11 if self.compact_mode else 16)
        axis.yaxis.label.set_color("#dbe6f3")
        axis.xaxis.label.set_color("#dbe6f3")

    def _load_thresholds(self) -> dict[str, float]:
        defaults = {
            "moderate_pressure_score": 2.0,
            "high_pressure_score": 4.0,
            "gpu_util_alert": 80.0,
            "free_ram_alert_gb": 2.0,
        }
        if not self.settings_path.exists():
            return defaults
        try:
            loaded = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return defaults
        return {key: float(loaded.get(key, value)) for key, value in defaults.items()}

    def _save_thresholds(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.thresholds, indent=2), encoding="utf-8")

    def _apply_thresholds(self) -> None:
        try:
            moderate = float(self.threshold_vars["moderate_pressure_score"].get())
            high = float(self.threshold_vars["high_pressure_score"].get())
            gpu_util = float(self.threshold_vars["gpu_util_alert"].get())
            free_ram = float(self.threshold_vars["free_ram_alert_gb"].get())
        except ValueError:
            messagebox.showerror("Invalid Threshold", "Threshold values must be numeric.")
            return
        if high < moderate:
            messagebox.showerror("Invalid Threshold", "High pressure must be greater than or equal to moderate pressure.")
            return
        self.thresholds = {
            "moderate_pressure_score": moderate,
            "high_pressure_score": high,
            "gpu_util_alert": gpu_util,
            "free_ram_alert_gb": free_ram,
        }
        self._save_thresholds()
        self.alert_var.set("Thresholds updated.")
        if self.last_sample is not None:
            self._set_alerts(self.last_pressure_score, self.last_sample)

    def _show_view(self, name: str) -> None:
        self.active_view.set(name)
        for frame in self.views.values():
            frame.grid_remove()
        self.views[name].grid()

    def _toggle_recording(self) -> None:
        if self.recording:
            self.recording = False
            if self.record_file is not None:
                self.record_file.close()
                self.record_file = None
            self.record_writer = None
            self.record_var.set("Recording: Off")
            return

        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        self.record_file = self.record_path.open("w", newline="", encoding="utf-8")
        self.record_writer = csv.DictWriter(
            self.record_file,
            fieldnames=[
                "timestamp",
                "cpu_util_percent",
                "gpu_util_percent",
                "gpu_shared_mb",
                "gpu_dedicated_mb",
                "gpu_total_committed_mb",
                "free_memory_gb",
                "top_engine",
                "engine_3d",
                "engine_compute",
                "engine_copy",
                "engine_video",
            ],
        )
        self.record_writer.writeheader()
        self.recording = True
        self.record_var.set(f"Recording: On ({self.record_path.name})")

    def _export_chart(self) -> None:
        current = self.active_view.get()
        output_path = self.record_path.parent / "gui_chart_snapshot.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if current == "ram":
            self.ram_figure.savefig(output_path, dpi=160, facecolor="#161b22", bbox_inches="tight")
            self.status_var.set(f"RAM chart exported to {output_path}")
        elif current == "gpu_focus":
            self.gpu_focus_figure.savefig(output_path, dpi=160, facecolor="#161b22", bbox_inches="tight")
            csv_path = self.record_path.parent / "gpu_focus_export.csv"
            self._export_gpu_focus_csv(csv_path)
            self.status_var.set(f"GPU Focus chart and CSV exported to {output_path.name}, {csv_path.name}")
        elif current == "gpu_cpu":
            self.gpu_cpu_figure.savefig(output_path, dpi=160, facecolor="#161b22", bbox_inches="tight")
            self.status_var.set(f"GPU/CPU chart exported to {output_path}")
        else:
            messagebox.showinfo("Overview Active", "Switch to GPU / CPU or RAM view before exporting a chart.")

    def _refresh_once(self) -> None:
        self._sample_and_update(schedule_next=False)

    def _set_alerts(self, pressure_score: int, sample: dict[str, float | str | None]) -> None:
        alerts: list[str] = []
        if pressure_score >= self.thresholds["high_pressure_score"]:
            alerts.append("High shared-memory pressure.")
        elif pressure_score >= self.thresholds["moderate_pressure_score"]:
            alerts.append("Moderate shared-memory pressure.")
        if sample["gpu_util_percent"] is not None and sample["gpu_util_percent"] > self.thresholds["gpu_util_alert"]:
            alerts.append(f"GPU utilization is above {self.thresholds['gpu_util_alert']:.0f}%.")
        if sample["free_memory_gb"] is not None and sample["free_memory_gb"] < self.thresholds["free_ram_alert_gb"]:
            alerts.append(f"Free RAM is below {self.thresholds['free_ram_alert_gb']:.1f} GB.")
        self.alert_var.set(" ".join(alerts) if alerts else "No active alerts.")

    def _update_gpu_cpu_chart(self) -> None:
        labels = list(self.history["labels"])
        cpu = [value if value is not None else 0 for value in self.history["cpu"]]
        gpu = [value if value is not None else 0 for value in self.history["gpu"]]
        self.gpu_cpu_ax.clear()
        self._style_axis(self.gpu_cpu_ax)
        self.gpu_cpu_ax.plot(labels, cpu, color="#58a6ff", linewidth=2.6, label="CPU %")
        self.gpu_cpu_ax.plot(labels, gpu, color="#ff7b72", linewidth=2.6, label="GPU %")
        self.gpu_cpu_ax.set_title("CPU and GPU Utilization", color="#f4f7fa")
        self.gpu_cpu_ax.set_ylabel("Percent", color="#dbe6f3")
        self.gpu_cpu_ax.set_xlabel("Sample Time", color="#dbe6f3")
        self.gpu_cpu_ax.set_ylim(0, 100)
        self.gpu_cpu_ax.legend(facecolor="#161b22", edgecolor="#425466", labelcolor="#dbe6f3", fontsize=9 if self.compact_mode else 11, loc="upper right")
        self._set_xticks(self.gpu_cpu_ax, labels)
        self.gpu_cpu_figure.tight_layout(pad=1.2 if self.compact_mode else 2.6)
        self.gpu_cpu_canvas.draw_idle()

    def _update_gpu_focus_chart(self) -> None:
        labels = list(self.history["labels"])
        series = [
            ("3D", list(self.history["engine_3d"]), "#ff7b72"),
            ("Compute", list(self.history["engine_compute"]), "#58a6ff"),
            ("Copy", list(self.history["engine_copy"]), "#d29922"),
            ("Video", list(self.history["engine_video"]), "#3fb950"),
        ]
        self.gpu_focus_ax.clear()
        self._style_axis(self.gpu_focus_ax)
        for label, values, color in series:
            plot_values = [value if value is not None else 0 for value in values]
            self.gpu_focus_ax.plot(labels, plot_values, linewidth=2.3, label=label, color=color)
        self.gpu_focus_ax.set_title("GPU Engine Utilization", color="#f4f7fa")
        self.gpu_focus_ax.set_ylabel("Percent", color="#dbe6f3")
        self.gpu_focus_ax.set_xlabel("Sample Time", color="#dbe6f3")
        self.gpu_focus_ax.set_ylim(0, 100)
        self.gpu_focus_ax.legend(facecolor="#161b22", edgecolor="#425466", labelcolor="#dbe6f3", fontsize=9 if self.compact_mode else 11, loc="upper right")
        self._set_xticks(self.gpu_focus_ax, labels)
        self.gpu_focus_figure.tight_layout(pad=1.2 if self.compact_mode else 2.6)
        self.gpu_focus_canvas.draw_idle()

    def _update_ram_chart(self) -> None:
        labels = list(self.history["labels"])
        ram = [value if value is not None else 0 for value in self.history["ram"]]
        shared = [value if value is not None else 0 for value in self.history["shared"]]
        dedicated = [value if value is not None else 0 for value in self.history["dedicated"]]
        self.ram_ax.clear()
        self.ram_ax_right.clear()
        self._style_axis(self.ram_ax)
        self._style_axis(self.ram_ax_right)
        left_line = self.ram_ax.plot(labels, ram, color="#3fb950", linewidth=2.6, label="Free RAM GB")
        right_shared = self.ram_ax_right.plot(labels, shared, color="#d29922", linewidth=2.6, label="GPU Shared MB")
        right_dedicated = self.ram_ax_right.plot(labels, dedicated, color="#58a6ff", linewidth=2.0, linestyle="--", label="GPU Dedicated MB")
        self.ram_ax.set_title("RAM and GPU Memory", color="#f4f7fa")
        self.ram_ax.set_ylabel("System RAM (GB)", color="#3fb950")
        self.ram_ax_right.set_ylabel("GPU Memory (MB)", color="#d29922")
        self.ram_ax.set_xlabel("Sample Time", color="#dbe6f3")
        legend_lines = left_line + right_shared + right_dedicated
        legend_labels = [line.get_label() for line in legend_lines]
        self.ram_ax.legend(legend_lines, legend_labels, facecolor="#161b22", edgecolor="#425466", labelcolor="#dbe6f3", fontsize=9 if self.compact_mode else 11, loc="upper right")
        self._set_xticks(self.ram_ax, labels)
        self._set_xticks(self.ram_ax_right, labels)
        self.ram_figure.tight_layout(pad=1.2 if self.compact_mode else 2.6)
        self.ram_canvas.draw_idle()

    def _set_xticks(self, axis, labels: list[str]) -> None:
        if not labels:
            return
        step = max(1, len(labels) // 8)
        tick_positions = list(range(0, len(labels), step))
        tick_labels = [labels[index] for index in tick_positions]
        axis.set_xticks(tick_positions, tick_labels)

    def _update_process_table(self) -> None:
        results = trace_gpu_processes(limit=12, include_idle=False)
        self.value_vars["active_gpu_procs"].set(str(len(results)))
        for tree in (self.proc_tree, self.gpu_focus_tree):
            for item in tree.get_children():
                tree.delete(item)
            for result in results:
                self.process_history[result.pid].append(result.total_util_percent)
                engine_summary = ", ".join(f"{name} {value:.2f}%" for name, value in list(result.engines.items())[:3]) or "idle"
                tree.insert(
                    "",
                    "end",
                    values=(f"{result.total_util_percent:.2f}", str(result.pid), result.name, engine_summary),
                    tags=("system",) if result.is_system else ("app",),
                )
            tree.tag_configure("system", foreground="#91a4b7")
            tree.tag_configure("app", foreground="#f4f7fa")

    def _on_gpu_focus_select(self, _event=None) -> None:
        selection = self.gpu_focus_tree.selection()
        if not selection:
            return
        item = self.gpu_focus_tree.item(selection[0])
        values = item.get("values", [])
        if len(values) < 3:
            return
        pid = int(values[1])
        history = list(self.process_history.get(pid, []))
        history_text = ", ".join(f"{value:.1f}" for value in history[-8:]) if history else "n/a"
        self.value_vars["selected_proc"].set(f"Selected: PID {pid}  {values[2]}  current GPU {values[0]}%")
        self.value_vars["selected_proc_history"].set(f"Recent GPU%: {history_text}")
        self._update_selected_process_chart(values[2], history)

    def _update_selected_process_chart(self, process_name: str, history: list[float]) -> None:
        self.proc_mini_ax.clear()
        self._style_axis(self.proc_mini_ax)
        self.proc_mini_ax.tick_params(labelsize=7 if self.compact_mode else 8)
        self.proc_mini_ax.set_title(f"{process_name} GPU%", color="#f4f7fa", fontsize=9 if self.compact_mode else 10)
        if history:
            x_values = list(range(len(history)))
            self.proc_mini_ax.plot(x_values, history, color="#58a6ff", linewidth=2.0)
            self.proc_mini_ax.fill_between(x_values, history, color="#58a6ff", alpha=0.15)
            upper = max(5.0, max(history) * 1.15)
            self.proc_mini_ax.set_ylim(0, upper)
        self.proc_mini_ax.set_xlabel("")
        self.proc_mini_ax.set_ylabel("")
        self.proc_mini_figure.tight_layout(pad=0.8)
        self.proc_mini_canvas.draw_idle()

    def _update_gpu_alerts(self, engine_sample, runtime_deltas: dict[str, float]) -> None:
        alerts: list[str] = []
        for engine_name, value in list(engine_sample.engines.items())[:3]:
            if value >= 40:
                alerts.append(f"{engine_name} spike {value:.1f}%")
        if runtime_deltas:
            top_runtime_name, top_runtime_value = max(runtime_deltas.items(), key=lambda item: item[1])
            self.value_vars["engine_runtime"].set(f"{top_runtime_name} +{top_runtime_value:.1f} ms")
            if top_runtime_value >= 100:
                alerts.append(f"{top_runtime_name} runtime +{top_runtime_value:.0f} ms")
        else:
            self.value_vars["engine_runtime"].set("Runtime delta: n/a")
        self.value_vars["gpu_alerts"].set(" | ".join(alerts) if alerts else "No GPU spikes.")

    def _export_gpu_focus_csv(self, csv_path: Path) -> None:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "timestamp",
            "gpu_util_percent",
            "gpu_shared_mb",
            "gpu_dedicated_mb",
            "gpu_total_committed_mb",
            "top_engine",
            "engine_3d",
            "engine_compute",
            "engine_copy",
            "engine_video",
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.gpu_focus_samples:
                writer.writerow({key: row.get(key) for key in fieldnames})

    def _sample_and_update(self, schedule_next: bool = True) -> None:
        uma_snapshot = inspect_uma()
        sample = collect_power_sample(self.counter_paths)
        self.last_sample = sample
        self.last_pressure_score = uma_snapshot.pressure_score
        label = sample["timestamp"].split()[-1]
        self.history["labels"].append(label)
        self.history["cpu"].append(sample["cpu_util_percent"])
        self.history["gpu"].append(sample["gpu_util_percent"])
        self.history["ram"].append(sample["free_memory_gb"])
        self.history["shared"].append(sample["gpu_shared_mb"])
        self.history["dedicated"].append(sample["gpu_dedicated_mb"])
        engine_sample = sample_gpu_engines(include_idle=False)
        running_times = sample_gpu_engine_running_times()
        runtime_deltas: dict[str, float] = {}
        if self.last_engine_running_times:
            for key, value in running_times.items():
                previous = self.last_engine_running_times.get(key, value)
                delta_ms = max(0.0, (value - previous) / 10000.0)
                if delta_ms > 0:
                    runtime_deltas[key] = round(delta_ms, 2)
        self.last_engine_running_times = running_times
        self.history["engine_3d"].append(engine_sample.engines.get("3d"))
        compute_total = sum(value for key, value in engine_sample.engines.items() if "compute" in key)
        copy_total = sum(value for key, value in engine_sample.engines.items() if "copy" in key)
        video_total = sum(value for key, value in engine_sample.engines.items() if "video" in key)
        self.history["engine_compute"].append(round(compute_total, 2) if compute_total else None)
        self.history["engine_copy"].append(round(copy_total, 2) if copy_total else None)
        self.history["engine_video"].append(round(video_total, 2) if video_total else None)

        self.value_vars["verdict"].set(uma_snapshot.verdict)
        self.value_vars["pressure"].set(str(uma_snapshot.pressure_score))
        self.value_vars["cpu"].set(f"{sample['cpu_util_percent']:.2f}%" if sample["cpu_util_percent"] is not None else "n/a")
        self.value_vars["gpu"].set(f"{sample['gpu_util_percent']:.2f}%" if sample["gpu_util_percent"] is not None else "n/a")
        self.value_vars["ram"].set(f"{sample['free_memory_gb']:.2f} GB" if sample["free_memory_gb"] is not None else "n/a")
        self.value_vars["shared"].set(f"{sample['gpu_shared_mb']:.2f} MB" if sample["gpu_shared_mb"] is not None else "n/a")
        self.value_vars["dedicated"].set(f"{sample['gpu_dedicated_mb']:.2f} MB" if sample["gpu_dedicated_mb"] is not None else "n/a")
        self.value_vars["committed"].set(f"{sample['gpu_total_committed_mb']:.2f} MB" if sample["gpu_total_committed_mb"] is not None else "n/a")
        if engine_sample.engines:
            top_engine_name, top_engine_value = next(iter(engine_sample.engines.items()))
            self.value_vars["top_engine"].set(f"{top_engine_name} {top_engine_value:.2f}%")
        else:
            self.value_vars["top_engine"].set("idle")
        self.gpu_focus_samples.append(
            {
                "timestamp": sample["timestamp"],
                "gpu_util_percent": sample["gpu_util_percent"],
                "gpu_shared_mb": sample["gpu_shared_mb"],
                "gpu_dedicated_mb": sample["gpu_dedicated_mb"],
                "gpu_total_committed_mb": sample["gpu_total_committed_mb"],
                "top_engine": self.value_vars["top_engine"].get(),
                "engine_3d": self.history["engine_3d"][-1],
                "engine_compute": self.history["engine_compute"][-1],
                "engine_copy": self.history["engine_copy"][-1],
                "engine_video": self.history["engine_video"][-1],
            }
        )
        self.status_var.set(f"Last sample: {sample['timestamp']}  |  refresh every {self.refresh_ms / 1000:.1f}s")
        self._set_alerts(uma_snapshot.pressure_score, sample)
        self._update_gpu_alerts(engine_sample, runtime_deltas)
        self._update_gpu_focus_chart()
        self._update_gpu_cpu_chart()
        self._update_ram_chart()
        self._update_process_table()

        if self.recording and self.record_writer is not None and self.record_file is not None:
            self.record_writer.writerow(
                {
                    "timestamp": sample["timestamp"],
                    "cpu_util_percent": sample["cpu_util_percent"],
                    "gpu_util_percent": sample["gpu_util_percent"],
                    "gpu_shared_mb": sample["gpu_shared_mb"],
                    "gpu_dedicated_mb": sample["gpu_dedicated_mb"],
                    "gpu_total_committed_mb": sample["gpu_total_committed_mb"],
                    "free_memory_gb": sample["free_memory_gb"],
                    "top_engine": self.value_vars["top_engine"].get(),
                    "engine_3d": self.history["engine_3d"][-1],
                    "engine_compute": self.history["engine_compute"][-1],
                    "engine_copy": self.history["engine_copy"][-1],
                    "engine_video": self.history["engine_video"][-1],
                }
            )
            self.record_file.flush()

        if schedule_next:
            self.root.after(self.refresh_ms, self._sample_and_update)

    def _on_close(self) -> None:
        if self.record_file is not None:
            self.record_file.close()
            self.record_file = None
        self.root.destroy()

    def run(self) -> None:
        self._sample_and_update()
        self.root.mainloop()


def launch_gui(refresh: float, record_path: Path) -> None:
    app = AmdApuGui(refresh, record_path)
    app.run()
