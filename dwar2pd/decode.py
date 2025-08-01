"""
Decoder for idcodes to SMILES conversion.
Uses the unified decode.mjs script.
"""

import pathlib
import subprocess
import sys
from typing import List, Optional


def decode_idcodes(idcodes: List[str]) -> List[Optional[str]]:
    """Decode multiple idcodes using the unified decode.mjs script."""
    if not idcodes:
        return []

    # Filter out empty ID codes
    valid_idcodes = [ic for ic in idcodes if ic and ic.strip()]
    if not valid_idcodes:
        return [None] * len(idcodes)

    try:
        # Run unified decode script
        script_path = pathlib.Path(__file__).parent / 'decode.mjs'
        result = subprocess.run(
            ["node", str(script_path)] + valid_idcodes,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        # Parse results: "index:smiles" format
        results = [None] * len(idcodes)
        for line in result.stdout.splitlines():
            if ':' in line:
                index_str, smiles = line.split(':', 1)
                if not smiles.startswith('ERROR:'):
                    batch_index = int(index_str)
                    # Map back to original position - handle duplicates by assigning to ALL matching positions
                    decoded_idcode = valid_idcodes[batch_index]
                    for i, orig_idcode in enumerate(idcodes):
                        if orig_idcode == decoded_idcode:
                            results[i] = smiles

        return results

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f"Decoding failed: {e}", file=sys.stderr)
        return [None] * len(idcodes)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return [None] * len(idcodes)
