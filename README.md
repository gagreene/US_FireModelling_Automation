# US Fire Modelling Automation

Python utilities for preparing and running the Missoula Fire Sciences Laboratory FireBehaviorModels command-line applications on Windows.

## Supported applications

- FlamMap
- MTT
- TOM
- Farsite
- Randig
- FSPro

The main module is `src/flame_components/flammap_cli.py`. It downloads the current vendor package when needed, creates landscapes and FlamMap-family input files, and invokes vendor executables.

## Requirements

- Windows
- Python 3.10 or later
- Conda is recommended
- Python packages used by the module: `rasterio`, `requests`, and `psutil`

Create an environment from the supplied Conda specification:

```powershell
conda create --name firemodelling --file conda-spec-file-windows.txt
conda activate firemodelling
```

Install the repository as an editable package before using its examples:

```powershell
python -m pip install --editable .
```

## Supporting data

`download_apps()` downloads `FireBehaviorModels.zip` and extracts it to `supporting_data/FB/`. The directory contains vendor executables in `bin/` and vendor sample data in `sampledata/`. It is ignored by Git; an optional prior package belongs in `supporting_data/FB_old/`.

For an editable checkout, `supporting_data/` at the repository root is the default. For a normal installed package, the default is `%LOCALAPPDATA%\flame_components\supporting_data`. Set `FLAME_COMPONENTS_DATA_DIR` before importing `flame_components` to use another writable location.
## Basic workflow

1. Create an LCP landscape with `gen_lcp()` or `gen_lcp_gdal()`.
2. Create a model input file.
3. Run the selected executable with `run_app()`.

FlamMap, MTT, TOM, and Farsite use `gen_flammap_input_file()` and `gen_command_file()`:

```python
from flame_components import flammap_cli as fm

input_path = fm.gen_flammap_input_file(
    out_dir='outputs',
    out_name='flammap_run',
    app_select='FlamMap',
    fuel_moisture_data=(1, '0 4 6 9 60 90'),
)

command_path = 'outputs/flammap_run_command.txt'
fm.gen_command_file(
    out_path=command_path,
    command_list=[['landscape.tif', input_path, 'outputs/flammap_run']],
)

stdout, stderr = fm.run_app('FlamMap', command_path)
```

## Randig and FSPro

Randig and FSPro are integrated as direct-argument applications. Their executables do not consume FlamMap command files.

```python
# Randig: landscape, Randig input file, output base
fm.run_app('Randig', [
    'landscape.tif',
    'randig.input',
    'outputs/randig_run',
])

# FSPro: landscape, FSPro input file, output base, ignition shapefile, barrier path or 0
fm.run_app('FSPro', [
    'landscape.tif',
    'fspro.input',
    'outputs/fspro_run',
    'ignition.shp',
    '0',
])
```

`app_test('Randig')` and `app_test('FSPro')` run the vendor sample datasets. These are long-running model executions and are not suitable for automated CI.

Use `gen_randig_input_file()` and `gen_fspro_input_file()` to create vendor-format input files. Randig and FSPro model runs remain manual workstation checks because the vendor executables can take several minutes or longer.

## Tests and examples

- `tests/test_flammap_cli.py` contains automated coverage for downloader, executable discovery, headers, and launcher argument construction.
- `examples/` contains user-facing Farsite, MTT, Randig, and FSPro drivers. They run vendor applications and should be launched manually as modules, for example `python -m examples.farsite_example`.
- Vendor smoke tests can take several minutes or longer and must remain outside pytest and GitHub Actions.

Run the automated test module with the interpreter configured for this project:

```powershell
python -m pytest tests\test_flammap_cli.py -v
```

## Notes

- Generated model outputs should be stored outside committed fixtures.
- Ignition and barrier shapefiles require their companion `.dbf`, `.prj`, and `.shx` files and must match the LCP projection.
- `gen_flammap_input_file()` supports FlamMap, MTT, TOM, and Farsite. Use `gen_randig_input_file()` or `gen_fspro_input_file()` for those separate vendor schemas.