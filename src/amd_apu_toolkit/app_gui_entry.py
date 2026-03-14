from __future__ import annotations

from pathlib import Path

from .gui import launch_gui


def main() -> None:
    launch_gui(refresh=2.0, record_path=Path("output/gui_live_trace.csv"))


if __name__ == "__main__":
    main()
