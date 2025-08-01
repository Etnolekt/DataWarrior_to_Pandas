"""
dwar2pd - A package for parsing DataWarrior (.dwar) files into pandas DataFrames.
"""

import logging
import subprocess
from pathlib import Path

from .parser import LoadDwar, get_dwar_info

logger = logging.getLogger(__name__)


def _check_node_dependencies():
    """Check if Node.js and required dependencies are available."""
    try:
        # Check if Node.js is available
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Node.js version: {result.stdout.strip()}")

        # Check if the decode script exists
        script_path = Path(__file__).parent / 'decode.mjs'
        if not script_path.exists():
            raise FileNotFoundError(f"Required script not found: {script_path}")

        # Check if node_modules exists
        node_modules_path = Path(__file__).parent / 'node_modules'
        if not node_modules_path.exists():
            raise FileNotFoundError(f"Node.js dependencies not found: {node_modules_path}")

        logger.info("All Node.js dependencies are available")

    except subprocess.CalledProcessError as e:
        logger.error(f"Node.js not available: {e}")
        raise RuntimeError("Node.js is required but not available. Please install Node.js.") from e
    except FileNotFoundError as e:
        logger.error(f"Missing dependency: {e}")
        raise RuntimeError(f"Missing required dependency: {e}") from e


# Check dependencies on import
_check_node_dependencies()

__all__ = ["LoadDwar", "get_dwar_info"]
