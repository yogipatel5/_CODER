import importlib
import inspect
from pathlib import Path

# Get all .py files in the signals directory
signals_dir = Path(__file__).parent
signal_files = [f.stem for f in signals_dir.glob("*.py") if f.is_file() and f.stem != "__init__"]

# Import each signal file and get all signal handlers
for module_name in signal_files:
    module = importlib.import_module(f"print.signals.{module_name}")

    # Get all functions from the module that are signal handlers
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and hasattr(obj, "is_signal_handler"):
            # Add the signal handler to this module's namespace
            globals()[name] = obj

# Clean up namespace
del Path, importlib, inspect, signals_dir, signal_files
