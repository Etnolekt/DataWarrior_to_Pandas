#!/usr/bin/env python3
"""
Command-line interface for dwar2pd.
"""

import argparse
import os
import sys

from .parser import LoadDwar, get_dwar_info


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Convert DWAR files to CSV with SMILES decoding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  dwar2pd input.dwar --output output.csv
  dwar2pd input.dwar --keep-structures
  dwar2pd input.dwar --info
        """
    )

    parser.add_argument('input_file', help='Input DWAR file path')
    parser.add_argument('--output', '-o', help='Output CSV file path')
    parser.add_argument('--keep-structures', action='store_true',
                       help='Keep original structure columns in output')
    parser.add_argument('--info', action='store_true',
                       help='Show file information only')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found")
        sys.exit(1)

    try:
        if args.info:
            # Show file information
            info = get_dwar_info(args.input_file)
            print(f"File: {args.input_file}")
            print(f"Rows: {info['rows']}")
            print(f"Columns: {info['columns']}")
            print(f"Structure columns: {info['structure_columns']}")
        else:
            # Load and convert the file
            df = LoadDwar(args.input_file, exclude_structure_columns=not args.keep_structures)

            if df.empty:
                print("Error: No data found in DWAR file")
                sys.exit(1)

            # Save to CSV
            output_file = args.output or f"{os.path.splitext(args.input_file)[0]}.csv"
            df.to_csv(output_file, index=False)
            print(f"Successfully converted {len(df)} rows to {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
