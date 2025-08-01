# DataWarrior_to_Pandas

A Python package loading [DataWarrior](https://openmolecules.org/datawarrior/) (`.dwar`) files into pandas DataFrames with SMILES decoding capabilities.
**dwar2pd** is a simple tool for importing `dwar` files directly into a pandas DataFrame, similar to how the `PandasTools` module from RDKit facilitates reading SDF files.

`dwar` files are widely used in drug discovery due to their ability to store comprehensive annotations and flexible metadata. Traditionally, converting these files for modeling applications, such as machine learning, requires intermediate steps like exporting to SDF or TSV formats and using tools like `PandasTools`. **dwar2pd** streamlines this process by enabling direct import of  files into pandas DataFrames, improving efficiency and reproducibility in data workflows.


## Features

- Parse DataWarrior (.dwar) files into pandas DataFrames
- Automatic SMILES decoding of molecular structures using [OpenChemLib](https://github.com/cheminfo/openchemlib-js). It handles many columns containing structures, such as scaffolds and R-groups
- Command-line interface for easy file conversion


## Prerequisites

Before installing `dwar2pd`, you need to have the Node.js (for SMILES decoding) installed:

```bash
node --version
npm --version
```

If Node.js is not installed, you can install it from [nodejs.org](https://nodejs.org/) or using your system's package manager:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nodejs npm
```

## Installation


### Step 1: Create a virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate 
```

### Step 2: Install the Python package
```bash
pip install -e .
```

### Step 3: Install Node.js dependencies
```bash
cd dwar2pd
npm install
```

## Usage

### Command Line Interface

The package provides a command-line tool `dwar2pd` for easy file conversion:

#### Basic conversion

```bash
dwar2pd input.dwar --output output.csv
```

## Python API

#### Basic usage
```python
from dwar2pd import LoadDwar

# Load DWAR file into pandas DataFrame
df = LoadDwar("input.dwar")

# The DataFrame now contains decoded SMILES in a "Structure_SMILES" column
print(df.head())
```

## How it works

1. **File Parsing**: The package reads DataWarrior files and extracts column properties and data
2. **Structure Detection**: Identifies columns containing molecular structures e.g. Structure, Scaffolds, R-groups (ID_code format)
3. **SMILES Decoding**: Uses OpenChemLib to convert IDCodes to SMILES strings
4. **DataFrame Creation**: Creates a pandas DataFrame with decoded SMILES in a new column



