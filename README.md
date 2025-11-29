# US Fire Modelling Automation

This repository provides a Python module and scripts to automate running fire behaviour models from the Missoula Fire Sciences Laboratory via a command\-line interface. The primary module is `flammap_cli.py`, which supports generating landscape files \(`.lcp`\), creating command and input files, and invoking applications such as FlamMap, MTT, TOM, and FARSITE on Windows.

## Status

- Target OS: Windows
- Primary language: Python
- Package manager: Conda
- Entry point: `flammap_cli.py`
- Data and executables are downloaded on demand with `downloadApps()`
- Sample tests available via `appTest()`

## Features

- Download required application data and executables for Missoula Fire Lab tools
- Generate landscape \(`.lcp`\) files from required raster inputs
- Build command and input files for FlamMap, MTT, TOM, and FARSITE
- Run models via the command line
- Validate setup with sample datasets

## Requirements

- Python 3\.8\+
- Modules: `os`, `glob`, `subprocess`, `rasterio`, `typing`, `requests`, `psutil`, `zipfile`
- Windows environment with Conda recommended

## Installation

With Conda on Windows:
```bash
# windows
conda create --name myenv --file conda-spec-file-windows.txt
conda activate myenv