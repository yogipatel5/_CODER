# Type hints and docstrings
import json
from pathlib import Path
from typing import Any, Optional, cast


def process_data(
    input_list: list[str], config: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Process a list of strings and return a dictionary.

    Args:
        input_list: List of strings to process
        config: Optional configuration dictionary

    Returns:
        Processed data as dictionary
    """
    result = {
        "input_list": input_list,
    }

    # Variable type hints
    count: int = 0

    # Long line that might trigger E501
    really_long_string = "This is a really long string that might trigger the line length warning in some linters but we're ignoring E501"

    # Unused variable (should trigger F841)
    unused_var = 42

    # Missing type hints (should trigger mypy)
    def inner_function(param: int) -> int:
        return param + 1

    return result


# Class with inheritance
class DataProcessor:
    def __init__(self, data_path: Path):
        self.data_path = data_path

    def load_data(self) -> dict[str, Any]:
        with open(self.data_path) as f:
            return cast(dict[str, Any], json.load(f))
