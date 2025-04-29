
# FlamMap Command Line Interface (CLI) Module

`flammap_cli.py` provides a Python interface for running fire modeling simulations using applications developed by the Missoula Fire Lab. This module enables the setup, execution, and handling of various fire behavior models, including **FlamMap**, **MTT**, **TOM**, and **Farsite**, through a command-line interface.

## Features

- **Download Required Application Data**: Downloads necessary fire modeling application data and executable files.
- **Generate Landscape File**: Create landscape files (LCP) by merging required raster files.
- **Generate Command & Input Files**: Generate command and input files for running simulations with different fire models.
- **Run Fire Models**: Execute simulations for FlamMap, MTT, TOM, and Farsite via the command line.
- **Test Application**: Run sample datasets to validate installations and configurations.

## Requirements

- Python 3.6+
- Modules: `os`, `glob`, `subprocess`, `rasterio`, `typing`, `requests` (for `downloadApps` function), `shutil` (for file operations), and `zipfile` (for handling zip files).

## Installation

With pip...
```bash
pip install -r requirements.txt
```
With Conda (recommended)...
- for Windows:
```bash
conda create --name myenv --file conda-spec-file-windows.txt
```
- for Ubuntu (coming soon):
```bash
conda create --name myenv --file conda-spec-file-ubuntu.txt
```

## Usage

### Download Application Data

To download necessary files for running the applications, use:

```python
downloadApps()
```

### Generate Landscape File (LCP)

Use `genLCP` to create an LCP file from 8 input TIF files.

```python
genLCP(
    lcp_file="output.lcp",
    elev_path="elevation.tif",
    slope_path="slope.tif",
    aspect_path="aspect.tif",
    fbfm_path="fbfm.tif",
    cc_path="canopy_cover.tif",
    ch_path="canopy_height.tif",
    cbh_path="cbh.tif",
    cbd_path="cbd.tif"
)
```

### Generate Command and Input Files

To create a command file for a simulation, use `genCommandFile`:

```python
genCommandFile(
    out_path="command_file.txt",
    command_list=[["FlamMap", "input.lcp", "output.tif", "condition_file", "wind_file", "options"]],
    suppress_messages=False
)
```

To generate an input file for a specified fire model:

```python
genInputFile(
    out_folder="output_folder",
    out_name="input_file",
    app_select="FlamMap",
    output_list=["FLAMELENGTH", "SPREADRATE", "INTENSITY"],
    fuel_moisture_data=[3, "0 2 2 3 4 5"]
)
```

### Run Fire Modeling Applications

Execute a fire model using `runApp`:

```python
runApp(
    app_select="FlamMap",
    command_file_path="command_file.txt",
    suppress_messages=False
)
```

### Test Application with Sample Data

To run a sample dataset for a specific fire model:

```python
appTest(app_selection="FlamMap")
```

## Functions

### `downloadApps()`
Downloads necessary fire behavior modeling application data.

### `genLCP(lcp_file, elev_path, slope_path, aspect_path, fbfm_path, cc_path, ch_path, cbh_path, cbd_path)`
Generates an LCP (Landscape) file by merging multiple raster files.

### `genCommandFile(out_path, command_list, suppress_messages)`
Generates a command file for running a fire model.

### `genInputFile(out_folder, out_name, suppress_messages, app_select, ...)`
Generates an input file with parameters specific to the selected fire model.

### `runApp(app_select, command_file_path, suppress_messages)`
Runs the selected fire model using the generated command file.

### `appTest(app_selection)`
Tests the specified fire modeling application using sample data provided by the Missoula Fire Lab.

## License

This project is licensed under the MIT License.

## Author

Gregory A. Greene, map.n.trowel@gmail.com

## Command Line Application Citation

"Fire behavior and First Order Fire Effects calculations produced with the command line applications developed by the Missoula Fire Sciences Laboratory, Missoula, MT"
