from __future__ import annotations
import platform
import sys

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore

def main():
    print("System:", platform.platform())
    print("Python:", sys.version.replace("\n"," "))
    if psutil is not None:
        print("CPU count:", psutil.cpu_count(logical=True))
        vm = psutil.virtual_memory()
        print("RAM:", f"{vm.total/1024/1024/1024:.1f} GB")
    else:
        print("psutil not installed; install requirements.txt for richer info.")

if __name__ == "__main__":
    main()
