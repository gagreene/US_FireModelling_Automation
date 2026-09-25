# FB Package Core Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `flammap_cli.py` so it downloads, locates, and correctly invokes the new `FireBehaviorModels.zip` package (published at `https://www.alturassolutions.com/FB/FB_API.htm`), replacing every assumption baked in for the old `FB.zip` package layout.

**Architecture:** No new modules or classes. This is a targeted set of fixes inside the existing single-module `flammap_cli.py`, each isolated to one function or dict, each covered by a new pytest test in a new `tests/test_flammap_cli.py` file (the existing `tests/*.py` files are example driver scripts, not automated tests, and are left alone). One new private helper (`_buildAppEnv()`) is added for subprocess environment isolation.

**Tech Stack:** Python 3.12 (conda env `ProcessGeospatial`), pytest 9.x (already installed in the dev env; stdlib `unittest.mock` used for monkeypatching, no new dependency needed), `psutil`, `requests`, `rasterio`.

**Spec:** This plan's spec is the review conducted in-session against the downloaded `https://www.alturassolutions.com/FB/FireBehaviorModels.zip` (release 2026-09-21) and empirical runs of the new `runflammap.exe`, `runmtt.exe`, `runfarsite.exe`, `runrandig.exe`, `runfspro.exe` executables. No separate spec document exists; the "Global Constraints" below are the load-bearing facts extracted from that review.

## Global Constraints

- New download URL: `https://www.alturassolutions.com/FB/FireBehaviorModels.zip` (replaces `https://www.alturassolutions.com/FB/FB.zip`).
- The new zip has **no top-level wrapper folder** — `bin/`, `doc/`, `sampledata/`, `share/` sit at the zip root. It must be extracted into `fb_path` (`supplementary_data/FB`), not `supplementary_path` (`supplementary_data`), or the existing `fb_path`/`bin_path` globals will point at nothing after a fresh download.
- New vendor executable names (all under `bin/`, all **with** `.exe` extension — `subprocess.Popen` on Windows does NOT resolve a bare name without the extension, confirmed empirically): `runflammap.exe`, `runmtt.exe`, `runfarsite.exe`. (`runrandig.exe`, `runfspro.exe` are handled in the follow-up plan `2026-09-23-fb-package-randig-fspro.md`.)
- `SpatialFOFEM` (and `FConstMTT`, `DeadFuelCondition`) no longer exist in the vendor package at all — must be removed from `app_exe_dict`.
- Sample/test data moved from `FB/Test<App>/SampleData/` to `FB/sampledata/<App>/`. Command-file naming is inconsistent across apps: `FlamMapCommand.txt`, `MTTCommand.txt`, but `FarsiteCmd.txt`.
- `.input` file version-header strings changed:
  - `Farsite`: was `FARSITE INPUTS FILE VERSION 1.0` → now `Farsite-Inputs-File-Version-1`.
  - `MTT`/`TOM`: was `ShortTerm-Inputs-File-Version-1` → now `FlamMap-Inputs-File-Version-1` (the vendor's own MTT documentation states "MTT input files are an extension of the FlamMap Input files").
  - `FlamMap`: unchanged (`FlamMap-Inputs-File-Version-1`).
- Command-file *contents* (positional fields per run line) are unchanged: FlamMap = `[LCPName] [InputsFileName] [outputDirPath] [outputsType]`; MTT/Farsite = `[LCPName] [InputsFileName] [IgnitionFileName] [BarrierFileName] [outputDirPath] [outputsType]`. Confirmed against the new sample command files and against `runmtt.exe`/`runfarsite.exe` usage banners. No change needed to `genCommandFile()` or to how `tests/farsite_testing.py`/`tests/mtt_testing.py` build their command lists.
- The vendor exe now requires `GDAL_DATA`, `PROJ_LIB`, and (new) `WINDNINJA_DATA` environment variables pointing at `fb_path/share/gdal`, `fb_path/share/proj`, `fb_path/share/windninja` respectively (per the vendor's own `SetENV.bat`), and `bin_path` prepended to `PATH`. Confirmed by empirically running `runflammap.exe` in this dev environment: without env isolation, it inherited this shell's conda `GDAL_DRIVER_PATH` (pointing at a *different* conda env's GDAL plugin directory) and failed with `ERROR 1: Can't load requested DLL: ...\gdalplugins\gdal_FITS.dll`. `runApp()` currently passes no `env=` to `subprocess.Popen`, so it fully inherits the parent process's environment — this must change.
- Out of scope for this plan (see follow-up plan): `Randig`, `FSPro` selectability: neither uses the "one command file, many runs" model — both take positional CLI args directly, confirmed via each exe's own usage banner. Do not touch them here.
- Out of scope for this plan: deleting the stale old-package files already committed under `Supplementary_Data/FB/` (e.g. `TestFlamMap.exe`, `TestSpatialFOFEM.exe`, `Test*/SampleData/`). Re-running `downloadApps()` after this plan lands will add the new files alongside the old ones without removing them. That is a bulk deletion of tracked binaries and needs an explicit human decision (`git rm -r Supplementary_Data/FB/` before the next real download) — do not automate it as part of this plan.
- `runApp()` only calls `downloadApps()` when `os.path.exists(fb_path)` is `False` — it never checks *what's inside* `fb_path`. Two consequences to guard against explicitly: (1) `downloadApps()` must not create `fb_path` until the download has actually succeeded, or a failed first download leaves an empty `fb_path` behind that silently disables all future auto-downloads (Task 1 below fixes this by creating `fb_path` only in the success branch, right before extraction). (2) Because `Supplementary_Data/FB/` already exists in this repo today (the old package, committed to git), landing this plan will **not** by itself trigger a re-download — `os.path.exists(fb_path)` is already `True`. The manual `git rm -r Supplementary_Data/FB/` mentioned above (or manually calling `downloadApps()` once) is required before the new exe names actually resolve to real files on disk.

---

## File Structure

- Modify: `flammap_cli.py` — `downloadApps()`, `app_name_dict`, `app_exe_dict`, `genInputFile()` (version header block), `appTest()` (`app_testData_dict` + glob), `runApp()` (env isolation), plus one new private helper `_buildAppEnv()`.
- Create: `tests/test_flammap_cli.py` — new pytest suite covering every change above via mocking (no real network calls, no real vendor exe execution).
- Modify: `docs/CODEBASE.md` — update the file/dict references and gotchas that this plan makes stale.

---

## Task 1: Fix `downloadApps()` URL and extraction target

**Files:**
- Modify: `flammap_cli.py:41-79` (`downloadApps()`)
- Test: `tests/test_flammap_cli.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `downloadApps()` still takes no args, returns `None`. Behavior change only: hits the new URL and extracts into `fb_path`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_flammap_cli.py` with:

```python
import os
import sys
import types

import pytest

import flammap_cli as fm


def test_download_apps_uses_new_url_and_extracts_into_fb_path(tmp_path, monkeypatch):
    fake_supplementary = tmp_path / 'supplementary_data'
    fake_fb = fake_supplementary / 'FB'
    monkeypatch.setattr(fm, 'supplementary_path', str(fake_supplementary))
    monkeypatch.setattr(fm, 'fb_path', str(fake_fb))

    captured = {}

    def fake_get(url, stream=True):
        captured['url'] = url

        class FakeResponse:
            status_code = 200
            raw = object()

        return FakeResponse()

    def fake_copyfileobj(src, dst):
        dst.write(b'not-a-real-zip-but-thats-fine')

    class FakeZipFile:
        def __init__(self, path, mode):
            captured['zip_path'] = path

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def extractall(self, target):
            captured['extract_target'] = target

    fake_requests = types.SimpleNamespace(get=fake_get)
    fake_shutil = types.SimpleNamespace(copyfileobj=fake_copyfileobj)
    fake_zipfile = types.SimpleNamespace(ZipFile=FakeZipFile)
    monkeypatch.setitem(sys.modules, 'requests', fake_requests)
    monkeypatch.setitem(sys.modules, 'shutil', fake_shutil)
    monkeypatch.setitem(sys.modules, 'zipfile', fake_zipfile)

    fm.downloadApps()

    assert captured['url'] == 'https://www.alturassolutions.com/FB/FireBehaviorModels.zip'
    assert os.path.normpath(captured['extract_target']) == os.path.normpath(str(fake_fb))
    assert os.path.isdir(fake_fb)
    # the downloaded zip must be cleaned up afterward
    assert not os.path.exists(captured['zip_path'])


def test_download_apps_does_not_create_fb_path_on_failed_download(tmp_path, monkeypatch):
    # A failed download must NOT leave an empty fb_path behind - runApp()
    # decides whether to re-trigger downloadApps() purely by checking
    # os.path.exists(fb_path), so an empty leftover directory would
    # permanently (and silently) disable all future auto-downloads.
    fake_supplementary = tmp_path / 'supplementary_data'
    fake_fb = fake_supplementary / 'FB'
    monkeypatch.setattr(fm, 'supplementary_path', str(fake_supplementary))
    monkeypatch.setattr(fm, 'fb_path', str(fake_fb))

    def fake_get(url, stream=True):
        class FakeResponse:
            status_code = 404

        return FakeResponse()

    monkeypatch.setitem(sys.modules, 'requests', types.SimpleNamespace(get=fake_get))

    fm.downloadApps()

    assert not os.path.exists(fake_fb)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_flammap_cli.py -k test_download_apps -v`
Expected: `test_download_apps_uses_new_url_and_extracts_into_fb_path` FAILS — asserted URL (`.../FireBehaviorModels.zip`) does not equal the current hardcoded `.../FB.zip`, and `extract_target` does not equal `fb_path` (current code extracts into `supplementary_path`). `test_download_apps_does_not_create_fb_path_on_failed_download` PASSES even against the current code (it never touches `fb_path` on a failed download either) — it is a regression guard for Step 3's fix, not a bug demonstration; keep it, and confirm in Step 4 that it still passes after the fix.

- [ ] **Step 3: Fix `downloadApps()`**

Replace `flammap_cli.py:41-79` with:

```python
def downloadApps() -> None:
    import requests
    import shutil
    import zipfile

    # The URL of the zip file
    data_url = 'https://www.alturassolutions.com/FB/FireBehaviorModels.zip'

    # Ensure the parent folder exists. Deliberately do NOT create fb_path
    # itself yet: runApp() decides whether to call downloadApps() again by
    # checking os.path.exists(fb_path), so fb_path must stay absent unless
    # and until a download actually succeeds - otherwise a failed download
    # would leave an empty fb_path behind and silently disable all future
    # auto-download attempts.
    os.makedirs(supplementary_path, exist_ok=True)

    # Send an HTTP GET request to the URL
    print(f'Downloading FB data')
    response = requests.get(data_url, stream=True)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Path to save the downloaded zip file
        zip_file_path = os.path.join(supplementary_path, 'FireBehaviorModels.zip')

        # Open a local file in binary write mode and save the downloaded content
        with open(zip_file_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)

        print(f'Download complete: {zip_file_path}')

        # The zip has no top-level wrapper folder (bin/, doc/, sampledata/,
        # share/ sit at the zip root), so it must be extracted directly into
        # fb_path, not supplementary_path. Only create fb_path now that the
        # download itself has succeeded.
        os.makedirs(fb_path, exist_ok=True)
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(fb_path)

        print(f'Extraction complete: {fb_path}')

        # Delete the zip file after extraction
        os.remove(zip_file_path)
        print(f'Zip file removed: {zip_file_path}')
    else:
        print(f'Failed to download file: {response.status_code}')

    return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_flammap_cli.py -k test_download_apps -v`
Expected: Both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add flammap_cli.py tests/test_flammap_cli.py
git commit -m "fix: point downloadApps() at new FireBehaviorModels.zip and extract into fb_path"
```

---

## Task 2: Update `app_name_dict` / `app_exe_dict` for the new exe names

**Files:**
- Modify: `flammap_cli.py:22-38`
- Test: `tests/test_flammap_cli.py`

**Interfaces:**
- Consumes: `bin_path` (module global, unchanged).
- Produces: `app_name_dict`, `app_exe_dict` — same dict shape (`{app_select: str}`), new values. `SpatialFOFEM` key removed from both. `runApp()` (Task 5) and `appTest()` (Task 4) consume these unchanged by name.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_flammap_cli.py`:

```python
@pytest.mark.parametrize('app', ['FlamMap', 'MTT', 'TOM', 'Farsite'])
def test_app_exe_dict_points_to_dotexe_under_bin_path(app):
    path = fm.app_exe_dict[app]
    assert path.endswith('.exe')
    assert os.path.normpath(os.path.dirname(path)) == os.path.normpath(fm.bin_path)


def test_app_exe_dict_no_longer_has_removed_upstream_apps():
    assert 'SpatialFOFEM' not in fm.app_exe_dict
    assert 'SpatialFOFEM' not in fm.app_name_dict


def test_app_name_dict_matches_new_vendor_exe_basenames():
    assert fm.app_name_dict['FlamMap'] == 'runflammap'
    assert fm.app_name_dict['MTT'] == 'runmtt'
    assert fm.app_name_dict['TOM'] == 'runmtt'
    assert fm.app_name_dict['Farsite'] == 'runfarsite'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_flammap_cli.py -k "app_exe_dict or app_name_dict" -v`
Expected: FAIL — current `app_exe_dict` values have no `.exe` suffix and still contain `SpatialFOFEM`; current `app_name_dict` values are `TestFlamMap`/`TestMTT`/`TestFARSITE`.

- [ ] **Step 3: Fix the dicts**

Replace `flammap_cli.py:22-38` with:

```python
app_name_dict = {
    'FlamMap': 'runflammap',
    'MTT': 'runmtt',
    'TOM': 'runmtt',
    'Farsite': 'runfarsite',
}

app_exe_dict = {
    'FlamMap': os.path.join(bin_path, 'runflammap.exe'),
    'MTT': os.path.join(bin_path, 'runmtt.exe'),
    'TOM': os.path.join(bin_path, 'runmtt.exe'),
    'Farsite': os.path.join(bin_path, 'runfarsite.exe'),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_flammap_cli.py -k "app_exe_dict or app_name_dict" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add flammap_cli.py tests/test_flammap_cli.py
git commit -m "fix: update app_name_dict/app_exe_dict for new vendor exe names, drop SpatialFOFEM"
```

---

## Task 3: Fix `.input` file version-header strings in `genInputFile()`

**Files:**
- Modify: `flammap_cli.py:928-933`
- Test: `tests/test_flammap_cli.py`

**Interfaces:**
- Consumes: `genInputFile()`'s existing `app_select` parameter (`'FlamMap' | 'MTT' | 'TOM' | 'Farsite'`).
- Produces: same return value (`out_path: str`), only the second line of the written file's content changes.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_flammap_cli.py`:

```python
@pytest.mark.parametrize('app_select,expected_header', [
    ('FlamMap', 'FlamMap-Inputs-File-Version-1'),
    ('MTT', 'FlamMap-Inputs-File-Version-1'),
    ('TOM', 'FlamMap-Inputs-File-Version-1'),
    ('Farsite', 'Farsite-Inputs-File-Version-1'),
])
def test_gen_input_file_writes_correct_version_header(tmp_path, app_select, expected_header):
    out_path = fm.genInputFile(
        out_dir=str(tmp_path),
        out_name='test_input',
        suppress_messages=True,
        app_select=app_select,
    )
    with open(out_path) as f:
        f.readline()  # '#FLAMMAP INPUT FILE FOR test_input'
        version_line = f.readline().strip()
    assert version_line == expected_header
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_flammap_cli.py -k version_header -v`
Expected: FAIL for `MTT`, `TOM` (writes `ShortTerm-Inputs-File-Version-1`) and for `Farsite` (writes `FARSITE INPUTS FILE VERSION 1.0`). `FlamMap` passes already.

- [ ] **Step 3: Fix the header block**

Replace `flammap_cli.py:928-933`:

```python
            if app_select == 'FlamMap':
                file.write('FlamMap-Inputs-File-Version-1\n')
            elif app_select in ['MTT', 'TOM']:
                file.write('ShortTerm-Inputs-File-Version-1\n')
            else:
                file.write('FARSITE INPUTS FILE VERSION 1.0\n')
```

with:

```python
            if app_select == 'FlamMap':
                file.write('FlamMap-Inputs-File-Version-1\n')
            elif app_select in ['MTT', 'TOM']:
                # MTT/TOM input files are documented by the vendor as "an
                # extension of the FlamMap Input files" and use the same
                # version header as FlamMap.
                file.write('FlamMap-Inputs-File-Version-1\n')
            else:
                file.write('Farsite-Inputs-File-Version-1\n')
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_flammap_cli.py -k version_header -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add flammap_cli.py tests/test_flammap_cli.py
git commit -m "fix: update genInputFile() version headers for new MTT/Farsite input format"
```

---

## Task 4: Fix `appTest()` sample-data paths and command-file discovery

**Files:**
- Modify: `flammap_cli.py:1149-1177` (`appTest()`)
- Test: `tests/test_flammap_cli.py`

**Interfaces:**
- Consumes: `fb_path` (module global), `runApp()` (called with `(app_selection, command_file_path)`).
- Produces: `appTest(app_selection: str) -> None`, unchanged signature.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_flammap_cli.py`:

```python
def test_app_test_finds_command_file_named_with_command_suffix(tmp_path, monkeypatch):
    fb_root = tmp_path / 'FB'
    sample_dir = fb_root / 'sampledata' / 'FlamMap'
    sample_dir.mkdir(parents=True)
    cmd_file = sample_dir / 'FlamMapCommand.txt'
    cmd_file.write_text('dummy')
    monkeypatch.setattr(fm, 'fb_path', str(fb_root))

    captured = {}

    def fake_run_app(app_select, command_file_path, **kwargs):
        captured['app_select'] = app_select
        captured['path'] = command_file_path

    monkeypatch.setattr(fm, 'runApp', fake_run_app)

    fm.appTest('FlamMap')

    assert captured['app_select'] == 'FlamMap'
    assert os.path.normpath(captured['path']) == os.path.normpath(str(cmd_file))


def test_app_test_finds_command_file_named_with_cmd_suffix(tmp_path, monkeypatch):
    fb_root = tmp_path / 'FB'
    sample_dir = fb_root / 'sampledata' / 'Farsite'
    sample_dir.mkdir(parents=True)
    cmd_file = sample_dir / 'FarsiteCmd.txt'
    cmd_file.write_text('dummy')
    monkeypatch.setattr(fm, 'fb_path', str(fb_root))

    captured = {}

    def fake_run_app(app_select, command_file_path, **kwargs):
        captured['path'] = command_file_path

    monkeypatch.setattr(fm, 'runApp', fake_run_app)

    fm.appTest('Farsite')

    assert os.path.normpath(captured['path']) == os.path.normpath(str(cmd_file))


def test_app_test_raises_clear_error_when_no_command_file_present(tmp_path, monkeypatch):
    fb_root = tmp_path / 'FB'
    (fb_root / 'sampledata' / 'MTT').mkdir(parents=True)
    monkeypatch.setattr(fm, 'fb_path', str(fb_root))

    with pytest.raises(FileNotFoundError):
        fm.appTest('MTT')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_flammap_cli.py -k "app_test_finds or app_test_raises" -v`
Expected: FAIL — current `app_testData_dict` points at `TestFlamMap\SampleData` / `TestFARSITE\SampleData` (nonexistent under the fake `fb_path`), so `test_data_path` resolution and the `*Cmd.txt` glob both miss.

- [ ] **Step 3: Fix `appTest()`**

Replace `flammap_cli.py:1149-1177` with:

```python
def appTest(app_selection: str) -> None:
    """
    Function to run the Missoula Fire Lab Command Line Application test datasets
    :param app_selection: The name of the selected fire modelling application.
        Options are "FlamMap", "MTT", "TOM", "Farsite". Default = "FlamMap".
    :return: None
    """
    app_testData_dict = {
        'FlamMap': os.path.join(fb_path, 'sampledata', 'FlamMap'),
        'MTT': os.path.join(fb_path, 'sampledata', 'MTT'),
        'TOM': os.path.join(fb_path, 'sampledata', 'MTT'),
        'Farsite': os.path.join(fb_path, 'sampledata', 'Farsite'),
    }

    # Get the test application path
    test_data_path = app_testData_dict.get(app_selection, None)

    if test_data_path is not None:
        # Vendor sample data names the command file inconsistently per app:
        # "...Command.txt" for FlamMap/MTT, "...Cmd.txt" for Farsite.
        command_file_matches = (
            glob.glob(os.path.join(test_data_path, '*Command.txt'))
            or glob.glob(os.path.join(test_data_path, '*Cmd.txt'))
        )
        if not command_file_matches:
            raise FileNotFoundError(
                f'No command file (*Command.txt or *Cmd.txt) found in {test_data_path}'
            )
        command_file_path = command_file_matches[0]

        # Run the application
        runApp(app_selection, command_file_path)
    else:
        raise ValueError(f'Invalid application selection: Must be one of: {", ".join(app_name_dict.keys())}')

    return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_flammap_cli.py -k "app_test_finds or app_test_raises" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add flammap_cli.py tests/test_flammap_cli.py
git commit -m "fix: update appTest() for new sampledata/<App> layout and command-file naming"
```

---

## Task 5: Isolate the subprocess environment in `runApp()`

**Files:**
- Modify: `flammap_cli.py:1087-1146` (`runApp()`); add new helper `_buildAppEnv()` immediately above it.
- Test: `tests/test_flammap_cli.py`

**Interfaces:**
- Consumes: `fb_path`, `bin_path` (module globals).
- Produces: `_buildAppEnv() -> dict` — a full environment mapping suitable for `subprocess.Popen(..., env=...)`. `runApp()`'s public signature is unchanged.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_flammap_cli.py`:

```python
def test_run_app_passes_isolated_env_to_popen(tmp_path, monkeypatch):
    fb_root = tmp_path / 'FB'
    bin_root = fb_root / 'bin'
    bin_root.mkdir(parents=True)
    # runApp() checks os.path.exists(fb_path) to decide whether to call
    # downloadApps() - make it exist so the real network path is never hit.
    monkeypatch.setattr(fm, 'fb_path', str(fb_root))
    monkeypatch.setattr(fm, 'bin_path', str(bin_root))
    monkeypatch.setenv('GDAL_DRIVER_PATH', r'C:\some\other\env\gdalplugins')
    monkeypatch.setenv('PATH', r'C:\some\other\path')

    captured = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            captured['args'] = args
            captured['env'] = kwargs.get('env')
            captured['cwd'] = kwargs.get('cwd')

        def communicate(self):
            return 'out', 'err'

    class FakeProcess:
        def children(self, recursive=True):
            return []

    monkeypatch.setattr(fm.subprocess, 'Popen', FakePopen)
    monkeypatch.setattr(fm.psutil, 'Process', lambda pid: FakeProcess())

    command_file = tmp_path / 'cmd.txt'
    command_file.write_text('dummy')

    fm.runApp(
        'FlamMap',
        str(command_file),
        app_exe_path=str(bin_root / 'runflammap.exe'),
        suppress_messages=True,
    )

    env = captured['env']
    assert env is not None, 'runApp() must pass an explicit env= to subprocess.Popen'
    assert env['GDAL_DATA'] == os.path.join(str(fb_root), 'share', 'gdal')
    assert env['PROJ_LIB'] == os.path.join(str(fb_root), 'share', 'proj')
    assert env['WINDNINJA_DATA'] == os.path.join(str(fb_root), 'share', 'windninja')
    assert 'GDAL_DRIVER_PATH' not in env
    assert env['PATH'].startswith(str(bin_root) + ';')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_flammap_cli.py::test_run_app_passes_isolated_env_to_popen -v`
Expected: FAIL — `captured['env']` is `None` because current `runApp()` never passes `env=` to `Popen`.

- [ ] **Step 3: Add `_buildAppEnv()` and wire it into `runApp()`**

Insert immediately before `runApp()` (i.e. before `flammap_cli.py:1087`):

```python
def _buildAppEnv() -> dict:
    """
    Build a subprocess environment for the Missoula Fire Lab CLI apps.

    The vendor executables ship their own GDAL/PROJ/WindNinja data and must
    not inherit GDAL_DATA/PROJ_LIB/GDAL_DRIVER_PATH from the calling Python
    environment (e.g. a conda env with its own GDAL install via rasterio) -
    doing so causes the vendor exe to load mismatched GDAL driver DLLs and
    fail with errors like "Can't load requested DLL: .../gdalplugins/gdal_FITS.dll".
    This mirrors what the vendor's own SetENV.bat does.
    """
    env = os.environ.copy()
    env['PATH'] = f'{bin_path};{env.get("PATH", "")}'
    env['GDAL_DATA'] = os.path.join(fb_path, 'share', 'gdal')
    env['PROJ_LIB'] = os.path.join(fb_path, 'share', 'proj')
    env['WINDNINJA_DATA'] = os.path.join(fb_path, 'share', 'windninja')
    env.pop('GDAL_DRIVER_PATH', None)
    return env
```

Then in `runApp()`, replace the `subprocess.Popen(...)` call (`flammap_cli.py:1116-1122`):

```python
        app_cli = subprocess.Popen(
            [app_exe_path, command_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(command_file_path)
        )
```

with:

```python
        app_cli = subprocess.Popen(
            [app_exe_path, command_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(command_file_path),
            env=_buildAppEnv()
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_flammap_cli.py::test_run_app_passes_isolated_env_to_popen -v`
Expected: PASS

- [ ] **Step 5: Run the full new test file**

Run: `python -m pytest tests/test_flammap_cli.py -v`
Expected: All tests from Tasks 1-5 PASS.

- [ ] **Step 6: Commit**

```bash
git add flammap_cli.py tests/test_flammap_cli.py
git commit -m "fix: isolate GDAL/PROJ/WindNinja env vars when launching vendor CLI apps"
```

---

## Task 6: Update `docs/CODEBASE.md` to match the new package

**Files:**
- Modify: `docs/CODEBASE.md`

**Interfaces:**
- Consumes: nothing (documentation only).
- Produces: nothing consumed elsewhere.

- [ ] **Step 1: Update the "Key files and responsibilities" table**

In `docs/CODEBASE.md`, update the `downloadApps()`, `runApp()`, and `appTest()` rows in the function table to describe: the new URL, extraction into `fb_path`, the `_buildAppEnv()` helper and why it exists, and the new `sampledata/<App>` layout. Update the `app_name_dict` / `app_exe_dict` row to list `runflammap`/`runmtt`/`runfarsite` and note `SpatialFOFEM` was removed upstream.

- [ ] **Step 2: Update the "Implicit assumptions / gotchas" section**

Remove or rewrite the bullet about `runApp()`'s child-process kill / no env isolation (now fixed) and the bullet about `FSPro`/`SpatialFOFEM` being half-wired (`SpatialFOFEM` is now gone upstream entirely; `FSPro` status depends on whether the follow-up plan `2026-09-23-fb-package-randig-fspro.md` has landed — note that explicitly with a pointer to that plan file).

- [ ] **Step 3: Add a note pointing at the plans**

Add a short line noting that `development/plans/2026-09-23-fb-package-core-integration.md` and `development/plans/2026-09-23-fb-package-randig-fspro.md` document this migration in detail, for anyone who needs the full before/after reasoning.

- [ ] **Step 4: Commit**

```bash
git add docs/CODEBASE.md
git commit -m "docs: update CODEBASE.md for the new FireBehaviorModels.zip package layout"
```

---

## Self-Review

**Spec coverage:**
- New URL/extraction target → Task 1. ✓
- New exe names + `.exe` suffix + `SpatialFOFEM` removal → Task 2. ✓
- `.input` version headers (MTT/TOM, Farsite) → Task 3. ✓
- `sampledata/<App>` layout + inconsistent command-file naming → Task 4. ✓
- `GDAL_DATA`/`PROJ_LIB`/`WINDNINJA_DATA`/`GDAL_DRIVER_PATH`/`PATH` isolation → Task 5. ✓
- Command-file *contents* unchanged → verified, no task needed (already correct; covered by existing `tests/farsite_testing.py`/`tests/mtt_testing.py` example scripts, not modified). ✓
- Stale committed old-package binaries → explicitly called out as out of scope, needs a human `git rm` decision, not automated. ✓
- Randig/FSPro → explicitly out of scope, deferred to `development/plans/2026-09-23-fb-package-randig-fspro.md`. ✓
- Docs reference point (`docs/CODEBASE.md`) → Task 6. ✓

**Placeholder scan:** No `TBD`/`implement later`/"add appropriate error handling" phrasing present; every step has literal code.

**Type consistency:** `_buildAppEnv() -> dict` used exactly that way in Task 5's Popen call. `app_exe_dict`/`app_name_dict` shapes unchanged (`dict[str, str]`) across Tasks 2, 4, 5. `appTest(app_selection: str) -> None` and `runApp(app_select: str, command_file_path: str, ...)` signatures unchanged from the existing code, matched consistently in every test.

**Post-review revision (Codex):** An independent Codex review of this plan (and its follow-up, `2026-09-23-fb-package-randig-fspro.md`) flagged that Task 1's original draft created `fb_path` unconditionally *before* attempting the download, which would leave an empty `fb_path` behind after a failed download and permanently disable `runApp()`'s existence-check-based auto-retry. Task 1 has been revised to only create `fb_path` inside the success branch, immediately before extraction, with a regression-guard test (`test_download_apps_does_not_create_fb_path_on_failed_download`) added. The `-k` pytest selectors that used a literal `_or_` (which is not pytest's boolean OR — `pytest -k` requires `-k "a or b"`) have also been corrected throughout Tasks 2 and 4. A new Global Constraints bullet also makes explicit that this repo's already-committed `Supplementary_Data/FB/` will short-circuit `runApp()`'s auto-download check regardless of this plan, so a manual refresh is required before the new exe names resolve to real files.
