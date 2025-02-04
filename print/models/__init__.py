# Do not import models here, they are being autoloaded by apps.py

import importlib
import inspect
from pathlib import Path

# Get all .py files in the models directory
models_dir = Path(__file__).parent
model_files = [f.stem for f in models_dir.glob("*.py") if f.is_file() and f.stem != "__init__"]

# Import each model file and get all model classes
for module_name in model_files:
    module = importlib.import_module(f"print.models.{module_name}")

    # Get all classes from the module that are Django models
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and hasattr(obj, "_meta") and getattr(obj._meta, "app_label", None) == "print":
            # Add the model to this module's namespace
            globals()[name] = obj

# Clean up namespace
del Path, importlib, inspect, models_dir, model_files, module_name, name, obj
