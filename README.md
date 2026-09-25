# US Fire Modelling Automation

Python utilities for preparing and running the Missoula Fire Sciences Laboratory FireBehaviorModels command-line applications on Windows.

## Supported applications

- FlamMap
- MTT
- TOM
- Farsite
- Randig
- FSPro

The main module is `flammap_cli.py`. It downloads the current vendor package when needed, creates landscapes and FlamMap-family input files, and invokes vendor executables.

## Requirements

- Windows
- Python 3.8 or later
- Conda is recommended
- Python packages used by the module: `rasterio`, `requests`, and `psutil`

Create an environment from the supplied Conda specification:

```powershell
conda create --name firemodelling --file conda-spec-file-windows.txt
conda activate firemodelling
```

## Vendor package and local data

`downloadApps()` downloads `FireBehaviorModels.zip` and extracts it to:

```text
supplementary_data/FB/
```

That directory contains executable files in `bin/` and vendor sample data in `sampledata/`. It is ignored by Git. The previous local package, when retained, is stored at `supplementary_data/FB_old/` and is also ignored.

## Basic workflow

1. Create an LCP landscape with `genLCP()` or `genLCP_gdal()`.
2. Create a model input file.
3. Run the selected executable with `runApp()`.

FlamMap, MTT, TOM, and Farsite use `genInputFile()` and `genCommandFile()`:

```python
import flammap_cli as fm

input_path = fm.genInputFile(
    out_dir='outputs',
    out_name='flammap_run',
    app_select='FlamMap',
    fuel_moisture_data=(1, '0 4 6 9 60 90'),
)

command_path = fm.genCommandFile(
    out_dir='outputs',
    out_name='flammap_run',
    command_list=[['landscape.tif', input_path, 'outputs/flammap_run']],
)

stdout, stderr = fm.runApp('FlamMap', command_path)
```

## Randig and FSPro

Randig and FSPro are integrated as direct-argument applications. Their executables do not consume FlamMap command files.

```python
# Randig: landscape, Randig input file, output base
fm.runApp('Randig', [
    'landscape.tif',
    'randig.input',
    'outputs/randig_run',
])

# FSPro: landscape, FSPro input file, output base, ignition shapefile, barrier path or 0
fm.runApp('FSPro', [
    'landscape.tif',
    'fspro.input',
    'outputs/fspro_run',
    'ignition.shp',
    '0',
])
```

`appTest('Randig')` and `appTest('FSPro')` run the vendor sample datasets. These are long-running model executions and are not suitable for automated CI.

Use `gen_randig_input_file()` and `gen_fspro_input_file()` to create vendor-format input files. Randig and FSPro model runs remain manual workstation checks because the vendor executables can take several minutes or longer.

## Tests and examples

- `tests/test_flammap_cli.py` contains automated coverage for downloader, executable discovery, headers, and launcher argument construction.
- `tests/mtt_testing.py` and `tests/farsite_testing.py` are user-facing example drivers. They run vendor applications and should be launched manually.
- Vendor smoke tests can take several minutes or longer and must remain outside pytest and GitHub Actions.

Run the automated test module with the interpreter configured for this project:

```powershell
& 'C:\Users\ggreene\.conda\envs\ProcessGeospatial\python.exe' -m pytest tests\test_flammap_cli.py -v
```

## Notes

- Generated model outputs should be stored outside committed fixtures.
- Ignition and barrier shapefiles require their companion `.dbf`, `.prj`, and `.shx` files and must match the LCP projection.
- `gen_flammap_input_file()` supports FlamMap, MTT, TOM, and Farsite. Use `gen_randig_input_file()` or `gen_fspro_input_file()` for those separate vendor schemas.