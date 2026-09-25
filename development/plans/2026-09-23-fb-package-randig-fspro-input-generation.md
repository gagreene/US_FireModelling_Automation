# Randig and FSPro Input-File Generation Plan

## Goal

Add dedicated, validated input-file builders for the vendor's Randig and FSPro
applications. Keep `genInputFile()` limited to the FlamMap-family format.

## Evidence and constraints

- The current package is staged at `supplementary_data/FB` (release
  2026-09-21). Randig's `RandigInputs.txt` begins with
  `#Randig-Inputs-File-Version-1`; its sample contains `NUMFIRES`, `DURATION`,
  `SPOTPROBABILITY`, `SPOTTING_SEED`, `MTT_SPOT_DELAY`,
  `MINIMUMNUMBERFIRES`, `TARGETBURNPROPORTION`, fuel moisture, common fire
  behavior switches, and gridded-wind switches. The landscape is a positional
  argument to `runrandig.exe`, not an input-file field.
- The current FSPro sample does not use the older
  `FSPRO-Inputs-File-Version-4` header. It starts with Java-generated comment
  lines (`#FsPro Model Inputs[B@...`), then contains scalar settings, a wind
  direction/speed matrix, ERC classes, historical ERC streams, average and
  standard-deviation ERC streams, a current ERC stream, and an optional
  forecast section. Treat the `[B@...` suffix as unstable comment text; do
  not reproduce it in generated output.
- Read `doc/RandigInputFile.pdf` and `doc/FSProInputFile.pdf` in that package
  before coding to establish field order, units, valid ranges, and optionality.
  The checked-in plan must record any release-specific behavior confirmed by
  actually invoking `bin/runrandig.exe` and `bin/runfspro.exe`.
- Both builders return the generated `.input` path. Neither launches an app;
  callers use the existing direct-argument `runApp()` interface.
- Do not add `Randig` or `FSPro` branches to `genInputFile()`. Randig reuses
  extracted FlamMap-compatible section writers; FSPro remains a separate schema.

## Public interfaces

Add these functions to `flammap_cli.py` immediately after `genInputFile()`. This
is the single authoritative interface definition; the Resolution trials below
determine whether an optional `resolution` value is serialized, not whether the
parameter exists.

```python
def genRandigInputFile(
    out_dir: str,
    out_name: str,
    num_fires: int,
    duration: int,
    spot_probability: float,
    *,
    resolution: Optional[Union[int, float]] = None,
    spotting_seed: Optional[int] = None,
    mtt_spot_delay: Optional[int] = None,
    target_burn_proportion: Optional[float] = None,
    minimum_number_fires: Optional[int] = None,
    fuel_moisture_data: Optional[Union[list, tuple]] = None,
    foliar_moisture_content: Union[int, float] = 100,
    crown_fire_method: str = 'ScottReinhardt',
    wind_speed: Union[int, float] = 15,
    wind_direction: Union[int, float] = 270,
    spread_direction_from_max: Union[int, float] = 0,
    gridded_winds_generate: Optional[str] = None,
    gridded_winds_resolution: Optional[Union[int, float]] = None,
    raws_elevation: Optional[Union[int, float]] = None,
    raws_units: Optional[str] = None,
    raws_data: Optional[Union[list, tuple]] = None,
    conditioning_period_end: Optional[str] = None,
    suppress_messages: bool = False,
) -> str: ...

def genFSProInputFile(
    out_dir: str,
    out_name: str,
    duration: int,
    num_fires: int,
    max_lag: int,
    poly_degree: int,
    calm_value: Union[int, float],
    wind_directions: list,
    wind_speeds: list,
    wind_cell_values: list,
    erc_classes: list,
    historic_erc_values: list,
    avg_erc_values: list,
    stddev_erc_values: list,
    current_erc_values: list,
    forecast: Optional[list] = None,
    *,
    barrier_fill: int = 0,
    resolution: Optional[Union[int, float]] = None,
    crown_fire_method: str = 'Finney',
    save_perimeters: int = 1,
    suppress_messages: bool = False,
) -> str: ...
```

`genRandigInputFile()` does not take a landscape path, output base, fire-list,
or wind-grid path because those are direct `runrandig.exe` arguments.
`genFSProInputFile()` does not take LCP, output, ignition, or barrier paths
because they are direct `runfspro.exe` arguments. There is no
`CONDITIONING_PERIOD_START` parameter: only the documented and existing
`CONDITIONING_PERIOD_END` switch is supported.
## Tasks

### 1. Capture the current vendor format as a fixture source

1. Use `supplementary_data/FB` as the current fixture source; do not add
   its vendor binaries or sample data to Git.
2. Record the current Randig and FSPro sample input files, relevant PDFs or
   text documentation, and the usage output from `runrandig.exe` and
   `runfspro.exe` in the implementation notes.
3. Build a field table for each format with file key, Python parameter, type,
   allowed range, required/optional status, and dependent-count rule.
4. Compare the current and older samples. The current FSPro comment header and
   Randig's lack of a `Landscape` field are already known differences; retain
   the current behavior unless the PDFs or executable tests prove otherwise.

### 2. Add `genRandigInputFile()`

1. Write failing pytest cases for:
   - the exact `#Randig-Inputs-File-Version-1` header and the current control
     order (`NUMFIRES`, `DURATION`, probability, seed, spot delay, minimum
     fires, target burn proportion);
   - the current sample's fuel-moisture and gridded-wind blocks;
   - optional RAWS, conditioning, seed, target, and minimum-fire switches
     switches being emitted only when supplied;
   - invalid ranges and invalid booleans raising `ValueError` before a file is
     written;
   - a missing output directory raising `FileNotFoundError` rather than being
     swallowed.
2. Implement the builder using a single `with open(..., 'w', newline='\n')`
   block. Do not use the broad exception swallowing currently present in
   `genInputFile()`.
3. Validate at least these relationships before writing:
   `num_fires > 0`, `duration > 0`, probability values in `[0, 1]`, valid
   spot-delay values, and record counts matching their supplied multiline
   blocks.
4. Do not serialize a landscape path, output base, or output type: those are
   direct `runrandig.exe` arguments. Emit only documented input-file switches.
5. Run the focused tests and compare the generated sample-equivalent file with
   the vendor file after normalizing paths and line endings.

### 3. Add `genFSProInputFile()`

1. Write failing pytest cases for:
   - a stable generated comment header and the current scalar setting order;
   - direction and speed counts matching their lists;
   - a wind-cell matrix with one row per wind speed and one value per wind
     direction;
   - the documented fixed width of each ERC-class row;
   - `NumERCYears`, `NumWxPerYear`, and flattened historic ERC totals being
     internally consistent;
   - average, standard-deviation, current-year, and forecast record counts
     agreeing with their declared values;
   - valid binary barrier/perimeter flags; and
   - omission of the Java-specific `[B@...` artifact while retaining a comment
     header accepted by the current executable.
2. Implement the writer as a direct serialization of the current package's
   order. Derive count fields from validated list lengths rather than accepting
   duplicate count parameters from callers.
3. Validate all matrix dimensions and series lengths before opening the output
   file. Reject ragged matrices, mismatched ERC-year records, unsupported
   crown-fire methods, and values outside the vendor-documented ranges.
4. Preserve numbers as caller-provided values where possible; do not round or
   convert ERC data. Use one predictable formatter for scalar and tabular
   values so generated files have stable golden-test output.
5. Compare a generated vendor-sample-equivalent file to the current vendor
   sample after normalizing paths and line endings.

### 4. Prove compatibility with the executables

1. Add unit tests to `tests/test_flammap_cli.py`; use temporary directories and
   no network or vendor executables in pytest.
2. Add a manually run, documented smoke-check command for each new builder:
   generate an input file from current sample values, invoke `runApp()` with
   its LCP, generated input, and output path, and confirm a successful exit
   plus expected output files. These are deliberately excluded from pytest and
   GitHub Actions: they depend on the local vendor package and take minutes to
   complete. The Randig check uses `NUMFIRES: 10` and
   `MINIMUMNUMBERFIRES: 10`; its measured 2026-09-24 runtime was 300 seconds
   on the BlueMountain landscape. The FSPro check uses the verified one-fire baseline described in Section F.
3. Do not add the vendor package or generated output files to Git. Extend
   `.gitignore` only if these smoke checks create files inside the repository.

### 5. Add end-to-end example scripts

1. Create `tests/randig_testing.py` and `tests/fspro_testing.py`, following
   the structure of `tests/mtt_testing.py` and `tests/farsite_testing.py`.
   These are user-facing example drivers, not pytest test modules.
2. Each script must show the ordered workflow: select or create an LCP,
   generate an app-specific input file, prepare an output base path, and call
   `runApp()`.
3. `randig_testing.py` must demonstrate its required `lcp`, generated-input,
   and output-base arguments, and identify the optional fire-list and
   wind-grid arguments.
4. `fspro_testing.py` must demonstrate the required arguments plus optional
   ignition and barrier shapefile paths. It must note that shapefiles require
   their companion files and must match the LCP projection.
5. Use `genRandigInputFile()` and `genFSProInputFile()` rather than vendor
   sample inputs. Store generated outputs outside committed fixture paths and
   ensure they are ignored by Git.
6. Add prerequisites and execution instructions to each module docstring.
   Do not execute either script from pytest because each runs a vendor model.

### 6. Document and release

1. Update `docs/CODEBASE.md` with both builders, their separate schemas, and
   the fact that `runApp()` consumes their paths as direct positional args.
2. Update `genInputFile()` documentation to state that it intentionally does
   not support Randig or FSPro.
3. Add a short usage example for each new builder and its `runApp()` call to
   the README or a dedicated usage document.
4. Run the complete pytest file before committing. Run the manual vendor smoke
   checks only on a workstation with the local vendor package; do not add them
   to automated CI.

## Acceptance criteria

- Both builders produce current vendor-format files from documented Python
  inputs and return their paths.
- Invalid dimensions, counts, flags, and numeric ranges fail before output is
  written.
- Generated Randig and FSPro files pass their respective vendor executable
  smoke checks using the current package sample data.
- `tests/randig_testing.py` and `tests/fspro_testing.py` demonstrate complete,
  user-runnable workflows using generated input files and direct `runApp()`
  arguments.
- Existing FlamMap, MTT, TOM, Farsite, Randig, and FSPro launcher tests remain
  green.

## Mandatory review revisions

This section supersedes any conflicting provisional signature or task wording
above. It closes the documented contradictions before implementation begins.

### A. Resolve the two Resolution contradictions before writing a builder

**Randig.** `doc/RandigInputFile.pdf` describes `Resolution` as required, but
release 2026-09-21's `sampledata/Randig/RandigInputs.txt` omits it and
`runrandig.exe` accepts the landscape as argv[1]. Create temporary copies of
the current sample and run all trials from a temporary output directory:

1. Run the unmodified sample as the baseline.
2. Run the same file with `RESOLUTION: <native LCP cell size>` inserted in the
   position prescribed by the PDF.
3. Record the exit status, stdout/stderr, and output metadata for both runs.

Do not implement `genRandigInputFile()` until this produces one of these
recorded decisions:

| Result | Builder contract |
|---|---|
| Current sample succeeds without `RESOLUTION` | Keep the optional parameter for forward compatibility, but omit the switch by default and document native landscape resolution. |
| Current sample fails without it and succeeds with it | Keep `resolution` optional in the signature but raise `ValueError` when it is absent; emit it in the vendor-documented position when supplied. |
| Both succeed but produce materially different outputs | Keep `resolution: Optional[Union[int, float]] = None`; omit it by default and serialize it only when supplied, with a docstring explaining the compatibility behavior. |
| Both trials fail | Stop implementation, verify the vendor environment and LCP/sample paths, and obtain a successful vendor baseline before choosing a builder contract. |

**RESOLVED (2026-09-24):** The unmodified vendor sample with no `RESOLUTION` line was run with `NUMFIRES: 100` and completed successfully (`returncode 0`; `test_Timings.txt` reports "Number fires run: 100" and "Number fires failed: 0"). It burned 73.68% of burnable cells, below the 98% `TargetBurnProportion`, confirming it stopped at `NumFires`. It produced `test_FireSizeList.txt`, `test_FlamMapOutputs.tif`, `test_RandigOutputs.tif`, `test_FLP.txt`, `test_WindVectors.kml`, and `test_Embers.csv`. A separate 10-fire trial with `MINIMUMNUMBERFIRES: 10` also completed successfully in 300 seconds. **Builder contract: omit `resolution` by default (as reflected in the Public Interfaces signature); document that this vendor build uses native landscape resolution when it is omitted.** Before supporting emitted `RESOLUTION` in a generated file, still run and record the explicit-resolution trial described above, including its output comparison.

**FSPro Resolution: UNRESOLVED — implementation blocker.** A reduced-fire vendor baseline now completes successfully (one fire, about six minutes; see Section F). Run and record that same one-fire baseline with the `Resolution: 60` line removed. Do not choose FSPro serialization behavior until the paired comparison completes.

**FSPro.** `doc/FSProInputFile.pdf` calls `Resolution` deprecated and says that
FSPro uses native landscape resolution; the current `FSProInputs.txt` still
writes `Resolution: 60`. Run the vendor sample unchanged, then run a copy with
that line removed. Record the same evidence. The default builder must omit a
deprecated switch when the omission succeeds. If the current executable still
requires it, expose `resolution: Optional[Union[int, float]] = None`, emit it
only when supplied, and mark the parameter as release-compatibility support.
The scalar parameter order must mirror file order: `duration`, `num_fires`,
`max_lag`, `poly_degree`, `barrier_fill`, optional `resolution`,
`crown_fire_method`, `save_perimeters`.

### B. Share Randig and FlamMap-family serialization

Randig is an extension of the FlamMap input format. Before adding its public
builder, extract private, file-object writers from `genInputFile()`:

```python
def _write_fuel_moisture_section(file, fuel_moisture_data): ...
def _write_conditioning_and_raws_sections(
    file, cond_period_start, cond_period_end, raws_units, raws_elev, raws_data,
    weather_data_units, weather_data, wind_data_units, wind_data,
): ...
def _write_fire_behavior_and_gridded_wind_sections(
    file, spread_direction_from_north, spread_direction_from_max,
    gridded_wind_spd_file, gridded_wind_dir_file, gridded_wind_gen,
    gridded_wind_res, gridded_wind_diurnal, gridded_wind_diurnal_airtemp,
    gridded_wind_diurnal_cldcvr, gridded_wind_diurnal_long,
    gridded_wind_diurnal_date, gridded_wind_diurnal_time, wind_spd_units,
    wind_speed, wind_direction, foliar_mc, crown_fire_method,
): ...
```

`genInputFile()` and `genRandigInputFile()` must call these helpers. Preserve
existing FlamMap/MTT/TOM/Farsite output order byte-for-byte for supplied
values. The shared fire-behavior helper deliberately excludes
`NUMBER_PROCESSORS`: `genInputFile()` continues to write that line immediately
after the helper call, while `genRandigInputFile()` never writes it because the
current Randig sample does not contain it. Add regression tests that generate
representative FlamMap and Randig blocks and assert the shared switch lines
appear once, in their current order. Do not reuse these helpers for FSPro.

### C. Pin literal values and type style

- Use `Optional[...]` and `Union[...]` in all public signatures, matching the
  existing module's typing style. Do not use `int | None` or `float | None`.
- Randig validation uses the current Randig literal `ScottReinhardt`.
- FSPro validation accepts exactly the literals documented for FSPro:
  `Finney` and `ScottRheinhardt`. Do not silently normalize the misspelling;
  raise `ValueError` that lists the FSPro-specific allowed values.
- Every optional numeric field must use `is not None`, not truthiness, so valid
  zero values such as `MTT_SPOT_DELAY: 0`, `BarrierFill: 0`, and calm wind
  values are serialized.

### D. Add repository safety before fixtures are used

First implementation change:

```gitignore
/supplementary_data/FB/
```

Add a regression check only if repository policy supports it; otherwise verify
with `git check-ignore -v supplementary_data/FB/bin/runfspro.exe`. The
vendor package is a local fixture source and must never be staged.

### E. Exact implementation and verification sequence

1. Add the ignore rule and run the `git check-ignore` command above.
2. Before coding a builder, run its two Resolution trials from section A and
   record the results in a short "format decisions" subsection. Randig's
   no-resolution baseline is complete; complete its explicit-resolution trial
   before accepting serialized `resolution`. FSPro cannot proceed until a
   reduced-fire baseline and its no-resolution counterpart both complete.
3. Add the private shared writers and tests proving unchanged FlamMap-family
   output. Run:

   ```powershell
   & 'C:\Users\ggreene\.conda\envs\ProcessGeospatial\python.exe' -m pytest tests\test_flammap_cli.py -k "input or header" -v
   ```

4. Add failing Randig golden-file and validation tests, then implement
   `genRandigInputFile()` using the decision from section A. Run:

   ```powershell
   & 'C:\Users\ggreene\.conda\envs\ProcessGeospatial\python.exe' -m pytest tests\test_flammap_cli.py -k randig -v
   ```

5. Add failing FSPro golden-file, matrix-shape, ERC-count, deprecated-
   resolution, and exact-crown-method tests, then implement
   `genFSProInputFile()`. Run:

   ```powershell
   & 'C:\Users\ggreene\.conda\envs\ProcessGeospatial\python.exe' -m pytest tests\test_flammap_cli.py -k fspro -v
   ```

6. Add the two user-facing example scripts already specified in Task 5, then
   run the whole suite:

   ```powershell
   & 'C:\Users\ggreene\.conda\envs\ProcessGeospatial\python.exe' -m pytest tests\test_flammap_cli.py -v
   ```

7. Run each executable smoke test manually against generated files in a
   temporary output directory. Do not invoke it from pytest or GitHub Actions.
   Use Randig's verified `NUMFIRES: 10` and `MINIMUMNUMBERFIRES: 10` setup;
   its measured 300-second runtime is acceptable for a workstation smoke check.
   Treat any non-zero exit, missing output, or parser warning as a format
   decision failure rather than accepting the generated file.

### F. Vendor runtime behavior — long-running workloads

These applications can take substantial time because they compile results from many simulated fires and, for FSPro, many weather scenarios. Executable checks remain workstation-only manual tests, outside pytest and GitHub Actions.

**Completed baselines:**

- Randig completed with `NUMFIRES: 10` and `MINIMUMNUMBERFIRES: 10` in 300 seconds on 2026-09-24, with 10 fires run, zero failures, and the expected output set.
- Randig also completed at 100 fires in about 580 seconds.
- FSPro completed the vendor sample with `NumFires: 1` in about six minutes on 2026-09-24, producing its expected raster, shapefile, summary, and timing outputs.

**Larger workloads:** Randig runs at 500 and 1000 fires were stopped after long time limits before completion. They reached approximately 95% of their requested fire count and continued consuming CPU. Treat these as unverified long-running workloads on this landscape and environment, not as a confirmed defect or hang. Runtime depends on the landscape, fire count, weather inputs, and scenario count.

**Implication for this plan:**

- `tests/randig_testing.py` defaults to `NUMFIRES: 10` and `MINIMUMNUMBERFIRES: 10`; `tests/fspro_testing.py` defaults to `NumFires: 1`.
- Their docstrings state the measured baseline runtimes and exclude execution from pytest and GitHub Actions.
- Manual smoke checks use the same verified configurations. They confirm completion and expected outputs, with no fixed upper time limit imposed by CI.
- The remaining FSPro prerequisite is the paired one-fire Resolution comparison, not a completion baseline.

## Self-review checklist

- Randig no-`RESOLUTION` behavior is measured and recorded. The explicit-`RESOLUTION` trial remains outstanding before emitted optional `resolution` support is accepted.
- FSPro's deprecated Resolution behavior is measured and recorded. **NOT DONE:** rerun the completed one-fire baseline without `Resolution: 60`.
- Randig shares all FlamMap-compatible section writers; FSPro shares none.
- The FSPro crown-fire validation list is independent of the existing
  FlamMap-family list.
- The current package fixture directory is ignored before any `git add`.
- Unit tests are deterministic and vendor executable smoke checks are manual.
- Vendor runtime behavior and completed reduced-fire baselines are documented. The manual smoke checks and example scripts use verified small configurations, and neither runs under pytest or GitHub Actions.