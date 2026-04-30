from __future__ import annotations

import csv
import io
import time
from collections import deque
from pathlib import Path
from statistics import mean

from PIL import Image, ImageDraw, ImageFont
from rich.align import Align
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .opencl_probe import probe_opencl
from .power import build_counter_paths, collect_power_sample
from .uma import inspect_uma


def _status_style(score: int) -> str:
    if score >= 4:
        return "bold white on red"
    if score >= 2:
        return "bold black on yellow"
    return "bold white on dark_green"


def _sparkline(values: list[float | None], width: int = 18) -> str:
    ticks = "▁▂▃▄▅▆▇█"
    filtered = [value for value in values if value is not None]
    if not filtered:
        return "n/a"
    trimmed = filtered[-width:]
    low = min(trimmed)
    high = max(trimmed)
    if high == low:
        return ticks[0] * len(trimmed)
    chars = []
    for value in trimmed:
        index = round((value - low) / (high - low) * (len(ticks) - 1))
        chars.append(ticks[index])
    return "".join(chars)


def _fmt(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}{suffix}"


def _build_overview_panel(uma_snapshot, power_sample) -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column()
    table.add_row("Verdict", uma_snapshot.verdict)
    table.add_row("Pressure", str(uma_snapshot.pressure_score))
    table.add_row("CPU util", _fmt(power_sample["cpu_util_percent"], "%"))
    table.add_row("GPU util", _fmt(power_sample["gpu_util_percent"], "%"))
    table.add_row("Free RAM", _fmt(power_sample["free_memory_gb"], " GB"))
    table.add_row("GPU shared", _fmt(power_sample["gpu_shared_mb"], " MB"))
    return Panel(table, title="UMA + Power", border_style="green")


def _build_opencl_panel(opencl_result) -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="magenta")
    table.add_column()
    table.add_row("Platform", str(opencl_result.platform_name))
    table.add_row("Version", str(opencl_result.platform_version))
    table.add_row("Device", str(opencl_result.device_name))
    table.add_row("Compute units", str(opencl_result.max_compute_units))
    table.add_row("Unified memory", str(opencl_result.unified_memory))
    table.add_row("clinfo avg", _fmt(opencl_result.average_clinfo_ms, " ms"))
    return Panel(table, title="OpenCL", border_style="blue")


def _build_trend_panel(history: dict[str, deque[float | None]]) -> Panel:
    table = Table(show_header=True, header_style="bold yellow")
    table.add_column("Metric")
    table.add_column("Current")
    table.add_column("Avg")
    table.add_column("Trend")
    for key, label, suffix in [
        ("cpu", "CPU util", "%"),
        ("gpu", "GPU util", "%"),
        ("ram", "Free RAM", " GB"),
        ("shared", "GPU shared", " MB"),
    ]:
        values = list(history[key])
        numeric = [value for value in values if value is not None]
        current = values[-1] if values else None
        avg_value = mean(numeric) if numeric else None
        table.add_row(label, _fmt(current, suffix), _fmt(avg_value, suffix), _sparkline(values))
    return Panel(table, title="Rolling Trends", border_style="yellow")


def _build_alert_panel(uma_snapshot, power_sample) -> Panel:
    alerts: list[str] = []
    if uma_snapshot.pressure_score >= 4:
        alerts.append("High shared-memory pressure: close heavy tabs or apps before GPU workloads.")
    elif uma_snapshot.pressure_score >= 2:
        alerts.append("Moderate shared-memory pressure: watch for stutter under mixed CPU/GPU load.")
    if power_sample["gpu_util_percent"] is not None and power_sample["gpu_util_percent"] > 80:
        alerts.append("GPU utilization is very high.")
    if power_sample["free_memory_gb"] is not None and power_sample["free_memory_gb"] < 2:
        alerts.append("System free RAM is below 2 GB.")
    if not alerts:
        alerts.append("No active alerts.")
    return Panel("\n".join(alerts), title="Alerts", border_style="red")


def render_dashboard(uma_snapshot, power_sample, opencl_result, history: dict[str, deque[float | None]]) -> Layout:
    header_text = Text("AMD APU Live Dashboard", style=_status_style(uma_snapshot.pressure_score))
    subtitle = Text(f"Last sample: {power_sample['timestamp']}  |  Ctrl+C to exit", style="white")
    header = Panel(Align.left(Group(header_text, subtitle)), border_style="dark_green")

    layout = Layout()
    layout.split_column(
        Layout(header, size=3),
        Layout(name="body"),
        Layout(_build_alert_panel(uma_snapshot, power_sample), size=5),
    )
    layout["body"].split_row(
        Layout(_build_overview_panel(uma_snapshot, power_sample)),
        Layout(_build_trend_panel(history)),
        Layout(_build_opencl_panel(opencl_result)),
    )
    return layout


def _snapshot_state(counter_paths: list[str], opencl_result, history: dict[str, deque[float | None]]):
    uma_snapshot = inspect_uma()
    power_sample = collect_power_sample(counter_paths)
    history["cpu"].append(power_sample["cpu_util_percent"])
    history["gpu"].append(power_sample["gpu_util_percent"])
    history["ram"].append(power_sample["free_memory_gb"])
    history["shared"].append(power_sample["gpu_shared_mb"])
    return uma_snapshot, power_sample, opencl_result, history


def export_dashboard_snapshot(output_path: Path) -> Path:
    counter_paths = build_counter_paths()
    opencl_result = probe_opencl(iterations=1)
    history = {
        "cpu": deque([None], maxlen=20),
        "gpu": deque([None], maxlen=20),
        "ram": deque([None], maxlen=20),
        "shared": deque([None], maxlen=20),
    }
    uma_snapshot, power_sample, opencl_result, history = _snapshot_state(counter_paths, opencl_result, history)
    layout = render_dashboard(uma_snapshot, power_sample, opencl_result, history)

    buffer = io.StringIO()
    console = Console(record=True, width=160, file=buffer, force_terminal=False, color_system=None)
    console.print(layout)
    text = console.export_text(clear=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = text.splitlines() or ["AMD APU Live Dashboard"]
    font = ImageFont.load_default()
    line_height = 18
    max_width = max(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(line, font=font) for line in lines)
    image = Image.new("RGB", (int(max_width) + 30, line_height * len(lines) + 30), "#101418")
    draw = ImageDraw.Draw(image)
    y = 15
    for line in lines:
        draw.text((15, y), line, font=font, fill="#d7e3ec")
        y += line_height
    image.save(output_path)
    return output_path


def run_dashboard(refresh: float, record_path: Path | None = None) -> None:
    counter_paths = build_counter_paths()
    opencl_result = probe_opencl(iterations=1)
    history = {
        "cpu": deque(maxlen=20),
        "gpu": deque(maxlen=20),
        "ram": deque(maxlen=20),
        "shared": deque(maxlen=20),
    }
    csv_writer = None
    csv_handle = None
    if record_path is not None:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        csv_handle = record_path.open("w", newline="", encoding="utf-8")
        csv_writer = csv.DictWriter(
            csv_handle,
            fieldnames=["timestamp", "cpu_util_percent", "gpu_util_percent", "gpu_shared_mb", "free_memory_gb"],
        )
        csv_writer.writeheader()

    try:
        with Live(auto_refresh=False, screen=True) as live:
            while True:
                uma_snapshot, power_sample, opencl_result, history = _snapshot_state(counter_paths, opencl_result, history)
                if csv_writer is not None:
                    csv_writer.writerow(power_sample)
                    csv_handle.flush()
                live.update(render_dashboard(uma_snapshot, power_sample, opencl_result, history), refresh=True)
                time.sleep(refresh)
    finally:
        if csv_handle is not None:
            csv_handle.close()
