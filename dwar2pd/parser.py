"""
Parser for DataWarrior (.dwar) files.
"""

import logging
import re
import warnings
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .decode import decode_idcodes

logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore', category=FutureWarning, message='.*errors=\'ignore\'.*')


def is_dwar_file(content: str) -> bool:
    """Check if the file content is a DWAR file."""
    return '<datawarrior-fileinfo>' in content or '<column properties>' in content


def extract_column_properties(content: str) -> Dict[str, Dict]:
    """Extract column information from DWAR file header section."""
    column_info = {}
    lines = content.split('\n')
    in_column_properties = False
    current_column = None

    for line in lines:
        line = line.strip()

        # Start of column properties section
        if line == "<column properties>":
            in_column_properties = True
            continue
        elif line == "</column properties>":
            in_column_properties = False
            continue
        elif not in_column_properties:
            continue

        # Parse column properties
        if line.startswith('<columnName='):
            # Extract column name from XML-like format
            match = re.search(r'<columnName="([^"]+)">', line)
            if match:
                current_column = match.group(1)
                column_info[current_column] = {"type": "string"}

        elif line.startswith('<columnProperty=') and current_column:
            # Extract column properties
            match = re.search(r'<columnProperty="([^"]+)">', line)
            if match:
                prop = match.group(1)
                if 'specialType' in prop:
                    # Extract the special type
                    special_type = prop.split('specialType')[1].strip()
                    column_info[current_column]["specialType"] = special_type
                elif 'parent' in prop:
                    # Extract parent column
                    parent = prop.split('parent')[1].strip()
                    column_info[current_column]["parent"] = parent

    return column_info


def find_header_and_data_lines(content: str) -> Tuple[Optional[List[str]], List[List[str]]]:
    """Find header and data lines in DWAR file content."""
    lines = content.split('\n')
    data_lines = []
    header_line = None

    found_column_properties_end = False
    header_found = False

    for line in lines:
        line = line.strip()

        # Track column properties section
        if '<column properties>' in line:
            continue
        elif '</column properties>' in line:
            found_column_properties_end = True
            continue

        # Look for header line after column properties
        if (found_column_properties_end and line and '\t' in line and
            not line.startswith('<') and not line.startswith('>') and not header_found):
            parts = line.split('\t')
            if len(parts) >= 3:
                header_line = parts
                header_found = True
                continue

        # Look for data lines
        if (line and '\t' in line and not line.startswith('<') and
            not line.startswith('>') and not line.startswith('settings=')):
            # Only add data lines after we've found the header
            if header_found:
                data_lines.append(line.split('\t'))

    return header_line, data_lines


def find_idcode_columns_for_decoding(df: pd.DataFrame, column_info: Dict) -> Tuple[List[str], List[str]]:
    """
    Find columns that contain ID codes for decoding to SMILES.
    Only uses metadata - much simpler and more reliable.

    Returns:
        Tuple of (columns_to_decode, columns_to_remove)
        - columns_to_decode: Columns that should be converted to SMILES
        - columns_to_remove: Original ID code columns that should be removed after decoding
    """
    columns_to_decode = []
    columns_to_remove = []

    # Only decode columns with specialType 'idcode' from metadata
    if column_info:
        for col_name, col_props in column_info.items():
            if col_name in df.columns:
                special_type = col_props.get('specialType', '')
                if str(special_type).lower() == 'idcode':
                    columns_to_decode.append(col_name)
                    columns_to_remove.append(col_name)

    return columns_to_decode, columns_to_remove


def decode_structures_in_dataframe(df: pd.DataFrame, column_info: Dict = None) -> pd.DataFrame:
    """Decode structure columns in DataFrame to SMILES."""
    if column_info is None:
        column_info = {}

    # Find columns to decode
    columns_to_decode, _ = find_idcode_columns_for_decoding(df, column_info)

    if not columns_to_decode:
        logger.info("No structure columns found for decoding")
        return df

    logger.info(f"Found structure columns: {columns_to_decode}")

    for col in columns_to_decode:
        logger.info(f"Decoding structures in column: {col}")

        smiles_col = f"{col}_SMILES"
        idcodes = df[col].tolist()

        # Decode all idcodes in batch
        smiles_list = decode_idcodes(idcodes)
        df[smiles_col] = smiles_list

        successful_decodings = df[smiles_col].notna().sum()
        total_structures = df[col].notna().sum()

        logger.info(f"Successfully decoded {successful_decodings}/{total_structures} structures in {col}")

    return df


def LoadDwar(file_path: str, smiles_column: str = "Structure_SMILES",
             exclude_structure_columns: bool = True) -> pd.DataFrame:
    """
    Load a DWAR file into a pandas DataFrame.

    Args:
        file_path: Path to the DWAR file
        smiles_column: Name of the column to store SMILES (default: "Structure_SMILES")
        exclude_structure_columns: Whether to exclude structure columns (default: True)

    Returns:
        pandas DataFrame containing the DWAR data
    """
    logger.info(f"Parsing DWAR file: {file_path}")

    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    # Verify this is a DWAR file
    if not is_dwar_file(content):
        raise ValueError("File does not appear to be a valid DWAR file")

    # Extract header and data lines
    header_line, data_lines = find_header_and_data_lines(content)

    if not data_lines:
        logger.warning("No data found in DWAR file")
        return pd.DataFrame()

    # Extract column properties
    column_info = extract_column_properties(content)
    logger.info(f"Detected column properties: {column_info}")

    # Create DataFrame
    df = pd.DataFrame(data_lines)

    # Set column names
    if header_line and len(header_line) == len(df.columns):
        df.columns = [str(col) for col in header_line]
    else:
        # Use generic column names
        df.columns = [f"Column_{i}" for i in range(len(df.columns))]

    # Remove completely empty rows
    df = df.dropna(how='all')

    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns")

    # Decode structures to SMILES
    df = decode_structures_in_dataframe(df, column_info)

    # Remove ID code columns if requested
    if exclude_structure_columns:
        _, original_idcode_columns = find_idcode_columns_for_decoding(df, column_info)
        # Always remove coordinate columns by name
        coordinate_patterns = ['coordinate', 'coord', 'atomcoord', 'scaffoldatom']
        coordinate_columns = [col for col in df.columns if any(pat in str(col).lower() for pat in coordinate_patterns)]
        # Also remove columns named 'Smiles' (case-insensitive)
        smiles_columns = [col for col in df.columns if str(col).lower() == 'smiles']
        columns_to_remove = list(set(original_idcode_columns + coordinate_columns + smiles_columns))
        if columns_to_remove:
            logger.info(f"Found ID code/coordinate/Smiles columns to remove after decoding: {columns_to_remove}")
            df = df.drop(columns=columns_to_remove)
            logger.info(f"Removed original ID code/coordinate/Smiles columns: {columns_to_remove}")
        else:
            logger.info("No ID code/coordinate/Smiles columns detected for removal")

    # Remove fingerprint columns
    fp_columns = [col for col in df.columns if str(col).endswith('Fp')]
    if fp_columns:
        df = df.drop(columns=fp_columns)
        logger.warning(f"Removed fingerprint columns: {fp_columns}")

    return df


def get_dwar_info(file_path: str) -> Dict:
    """Get metadata information from a DWAR file."""
    logger.info(f"Getting file info for: {file_path}")

    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    info = {}

    # Extract version information
    version_match = re.search(r'version\s+(\S+)', content)
    if version_match:
        info['version'] = version_match.group(1)

    # Extract creation date
    created_match = re.search(r'created\s+(.+)', content)
    if created_match:
        info['created'] = created_match.group(1).strip()

    # Count data rows
    _, data_lines = find_header_and_data_lines(content)
    info['rowcount'] = len(data_lines)

    # Extract column information
    column_info = extract_column_properties(content)
    info['columns'] = column_info

    logger.info(f"File info: {info}")
    return info
