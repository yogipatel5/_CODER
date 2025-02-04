"""Auto-discover and import all models in this directory."""

import importlib
import inspect
import logging
from pathlib import Path

from django.db import models

logger = logging.getLogger(__name__)

# Get all .py files in the models directory
models_dir = Path(__file__).parent
model_files = [f.stem for f in models_dir.glob("*.py") if f.is_file() and f.stem != "__init__"]

# Import each model file and get all model classes
for module_name in model_files:
    try:
        module = importlib.import_module(f"pfsense.models.{module_name}")

        # Get all classes from the module that are Django models
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, models.Model)
                and obj.__module__ == f"pfsense.models.{module_name}"
            ):
                # Add the model to this module's namespace
                globals()[name] = obj
                logger.debug(f"Imported model {name} from {module_name}")
    except Exception as e:
        logger.error(f"Failed to import models from {module_name}: {str(e)}")

# Clean up namespace
del Path, importlib, inspect, models_dir, model_files, module_name, name, obj
