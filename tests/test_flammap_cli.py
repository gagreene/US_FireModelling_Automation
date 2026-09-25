import os
import sys
import types

import pytest

import flammap_cli as fm


def test_download_apps_uses_new_url_and_extracts_into_fb_path(tmp_path, monkeypatch):
    fake_supplementary = tmp_path / "supplementary_data"
    fake_fb = fake_supplementary / "FB"
    monkeypatch.setattr(fm, "supplementary_path", str(fake_supplementary))
    monkeypatch.setattr(fm, "fb_path", str(fake_fb))
    captured = {}

    def fake_get(url, stream=True):
        captured["url"] = url

        class FakeResponse:
            status_code = 200
            raw = object()

        return FakeResponse()

    def fake_copyfileobj(src, dst):
        dst.write(b"not-a-real-zip-but-thats-fine")

    class FakeZipFile:
        def __init__(self, path, mode):
            captured["zip_path"] = path

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def extractall(self, target):
            captured["extract_target"] = target

    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(get=fake_get))
    monkeypatch.setitem(
        sys.modules, "shutil", types.SimpleNamespace(copyfileobj=fake_copyfileobj)
    )
    monkeypatch.setitem(
        sys.modules, "zipfile", types.SimpleNamespace(ZipFile=FakeZipFile)
    )

    fm.download_apps()

    assert (
        captured["url"] == "https://www.alturassolutions.com/FB/FireBehaviorModels.zip"
    )
    assert os.path.normpath(captured["extract_target"]) == os.path.normpath(
        str(fake_fb)
    )
    assert os.path.isdir(fake_fb)
    assert not os.path.exists(captured["zip_path"])


def test_download_apps_does_not_create_fb_path_on_failed_download(
    tmp_path, monkeypatch
):
    fake_supplementary = tmp_path / "supplementary_data"
    fake_fb = fake_supplementary / "FB"
    monkeypatch.setattr(fm, "supplementary_path", str(fake_supplementary))
    monkeypatch.setattr(fm, "fb_path", str(fake_fb))

    def fake_get(url, stream=True):
        class FakeResponse:
            status_code = 404

        return FakeResponse()

    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(get=fake_get))
    fm.download_apps()
    assert not os.path.exists(fake_fb)


@pytest.mark.parametrize("app", ["FlamMap", "MTT", "TOM", "Farsite"])
def test_app_exe_dict_points_to_dotexe_under_bin_path(app):
    path = fm.app_exe_dict[app]
    assert path.endswith(".exe")
    assert os.path.normpath(os.path.dirname(path)) == os.path.normpath(fm.bin_path)


def test_app_exe_dict_no_longer_has_removed_upstream_apps():
    assert "SpatialFOFEM" not in fm.app_exe_dict
    assert "SpatialFOFEM" not in fm.app_name_dict


def test_app_name_dict_matches_new_vendor_exe_basenames():
    assert fm.app_name_dict["FlamMap"] == "runflammap"
    assert fm.app_name_dict["MTT"] == "runmtt"
    assert fm.app_name_dict["TOM"] == "runmtt"
    assert fm.app_name_dict["Farsite"] == "runfarsite"


@pytest.mark.parametrize(
    "app_select,expected_header",
    [
        ("FlamMap", "FlamMap-Inputs-File-Version-1"),
        ("MTT", "FlamMap-Inputs-File-Version-1"),
        ("TOM", "FlamMap-Inputs-File-Version-1"),
        ("Farsite", "Farsite-Inputs-File-Version-1"),
    ],
)
def test_gen_flammap_input_file_writes_correct_version_header(
    tmp_path, app_select, expected_header
):
    out_path = fm.gen_flammap_input_file(
        out_dir=str(tmp_path),
        out_name="test_input",
        suppress_messages=True,
        app_select=app_select,
    )
    with open(out_path) as file:
        file.readline()
        version_line = file.readline().strip()
    assert version_line == expected_header


def test_app_test_finds_command_file_named_with_command_suffix(tmp_path, monkeypatch):
    fb_root = tmp_path / "FB"
    sample_dir = fb_root / "sampledata" / "FlamMap"
    sample_dir.mkdir(parents=True)
    cmd_file = sample_dir / "FlamMapCommand.txt"
    cmd_file.write_text("dummy")
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    captured = {}

    def fake_run_app(app_select, command_file_path, **kwargs):
        captured["app_select"] = app_select
        captured["path"] = command_file_path

    monkeypatch.setattr(fm, "run_app", fake_run_app)
    fm.app_test("FlamMap")
    assert captured["app_select"] == "FlamMap"
    assert os.path.normpath(captured["path"]) == os.path.normpath(str(cmd_file))


def test_app_test_finds_command_file_named_with_cmd_suffix(tmp_path, monkeypatch):
    fb_root = tmp_path / "FB"
    sample_dir = fb_root / "sampledata" / "Farsite"
    sample_dir.mkdir(parents=True)
    cmd_file = sample_dir / "FarsiteCmd.txt"
    cmd_file.write_text("dummy")
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    captured = {}

    def fake_run_app(app_select, command_file_path, **kwargs):
        captured["path"] = command_file_path

    monkeypatch.setattr(fm, "run_app", fake_run_app)
    fm.app_test("Farsite")
    assert os.path.normpath(captured["path"]) == os.path.normpath(str(cmd_file))


def test_app_test_raises_clear_error_when_no_command_file_present(
    tmp_path, monkeypatch
):
    fb_root = tmp_path / "FB"
    (fb_root / "sampledata" / "MTT").mkdir(parents=True)
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    with pytest.raises(FileNotFoundError):
        fm.app_test("MTT")


def test_run_app_passes_isolated_env_to_popen(tmp_path, monkeypatch):
    fb_root = tmp_path / "FB"
    bin_root = fb_root / "bin"
    bin_root.mkdir(parents=True)
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    monkeypatch.setattr(fm, "bin_path", str(bin_root))
    monkeypatch.setenv("GDAL_DRIVER_PATH", r"C:\some\other\env\gdalplugins")
    monkeypatch.setenv("PATH", r"C:\some\other\path")
    captured = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            captured["args"] = args
            captured["env"] = kwargs.get("env")
            captured["cwd"] = kwargs.get("cwd")

        def communicate(self):
            return "out", "err"

    class FakeProcess:
        def children(self, recursive=True):
            return []

    monkeypatch.setattr(fm.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(fm.psutil, "Process", lambda pid: FakeProcess())
    command_file = tmp_path / "cmd.txt"
    command_file.write_text("dummy")
    fm.run_app(
        "FlamMap",
        str(command_file),
        app_exe_path=str(bin_root / "runflammap.exe"),
        suppress_messages=True,
    )
    env = captured["env"]
    assert env is not None
    assert env["GDAL_DATA"] == os.path.join(str(fb_root), "share", "gdal")
    assert env["PROJ_LIB"] == os.path.join(str(fb_root), "share", "proj")
    assert env["WINDNINJA_DATA"] == os.path.join(str(fb_root), "share", "windninja")
    assert "GDAL_DRIVER_PATH" not in env
    assert env["PATH"].startswith(str(bin_root) + ";")


@pytest.mark.parametrize(
    "app,exe_basename",
    [
        ("Randig", "runrandig.exe"),
        ("FSPro", "runfspro.exe"),
    ],
)
def test_app_exe_dict_includes_randig_and_fspro(app, exe_basename):
    assert fm.app_name_dict[app] == exe_basename[:-4]
    path = fm.app_exe_dict[app]
    assert os.path.basename(path) == exe_basename
    assert os.path.normpath(os.path.dirname(path)) == os.path.normpath(fm.bin_path)


def _mock_run_app_dependencies(tmp_path, monkeypatch):
    fb_root = tmp_path / "FB"
    bin_root = fb_root / "bin"
    bin_root.mkdir(parents=True)
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    monkeypatch.setattr(fm, "bin_path", str(bin_root))
    captured = {}

    class FakePopen:
        def __init__(self, args, **kwargs):
            captured["args"] = args
            captured["cwd"] = kwargs.get("cwd")
            captured["env"] = kwargs.get("env")

        def communicate(self):
            return "out", "err"

    class FakeProcess:
        def children(self, recursive=True):
            return []

    monkeypatch.setattr(fm.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(fm.psutil, "Process", lambda pid: FakeProcess())
    return fb_root, bin_root, captured


def test_run_app_accepts_list_of_positional_args_for_direct_style_apps(
    tmp_path, monkeypatch
):
    _fb_root, bin_root, captured = _mock_run_app_dependencies(tmp_path, monkeypatch)
    exe_path = str(bin_root / "runrandig.exe")
    positional_args = ["lcp.tif", "RandigInputs.txt", os.path.join("out", "test")]
    work_dir = str(tmp_path / "workdir")

    fm.run_app(
        "Randig",
        positional_args,
        app_exe_path=exe_path,
        cwd=work_dir,
        suppress_messages=True,
    )

    assert captured["args"] == [exe_path] + positional_args
    assert captured["cwd"] == work_dir
    assert captured["env"] is not None


def test_run_app_still_accepts_a_plain_command_file_string(tmp_path, monkeypatch):
    _, bin_root, captured = _mock_run_app_dependencies(tmp_path, monkeypatch)
    command_dir = tmp_path / "somedir"
    command_dir.mkdir()
    command_file = command_dir / "cmd.txt"
    command_file.write_text("dummy")
    exe_path = str(bin_root / "runflammap.exe")

    fm.run_app(
        "FlamMap", str(command_file), app_exe_path=exe_path, suppress_messages=True
    )

    assert captured["args"] == [exe_path, str(command_file)]
    assert os.path.normpath(captured["cwd"]) == os.path.normpath(str(command_dir))


def test_run_app_preserves_positional_argument_order_for_backward_compat(
    tmp_path, monkeypatch
):
    _, bin_root, captured = _mock_run_app_dependencies(tmp_path, monkeypatch)
    command_dir = tmp_path / "somedir"
    command_dir.mkdir()
    command_file = command_dir / "cmd.txt"
    command_file.write_text("dummy")
    fm.run_app("FlamMap", str(command_file), str(bin_root / "runflammap.exe"), True)

    assert os.path.normpath(captured["cwd"]) == os.path.normpath(str(command_dir))


def test_app_test_builds_positional_args_for_randig(tmp_path, monkeypatch):
    fb_root = tmp_path / "FB"
    (fb_root / "sampledata" / "BlueMountain").mkdir(parents=True)
    (fb_root / "sampledata" / "Randig" / "out").mkdir(parents=True)
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    captured = {}
    monkeypatch.setattr(
        fm,
        "run_app",
        lambda app_select, command_file_path, **kwargs: captured.update(
            app_select=app_select, args=command_file_path
        ),
    )

    fm.app_test("Randig")

    assert captured["app_select"] == "Randig"
    assert captured["args"] == [
        os.path.join(str(fb_root), "sampledata", "BlueMountain", "BlueMountain.tif"),
        os.path.join(str(fb_root), "sampledata", "Randig", "RandigInputs.txt"),
        os.path.join(str(fb_root), "sampledata", "Randig", "out", "test"),
    ]


def test_app_test_builds_positional_args_for_fspro(tmp_path, monkeypatch):
    fb_root = tmp_path / "FB"
    (fb_root / "sampledata" / "BlueMountain").mkdir(parents=True)
    (fb_root / "sampledata" / "FSPro" / "out").mkdir(parents=True)
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    captured = {}
    monkeypatch.setattr(
        fm,
        "run_app",
        lambda app_select, command_file_path, **kwargs: captured.update(
            app_select=app_select, args=command_file_path
        ),
    )

    fm.app_test("FSPro")

    assert captured["app_select"] == "FSPro"
    assert captured["args"] == [
        os.path.join(str(fb_root), "sampledata", "BlueMountain", "BlueMountain.tif"),
        os.path.join(str(fb_root), "sampledata", "FSPro", "FSProInputs.txt"),
        os.path.join(str(fb_root), "sampledata", "FSPro", "out", "test"),
        os.path.join(str(fb_root), "sampledata", "BlueMountain", "centerIgnit.shp"),
        "0",
    ]


def test_app_test_still_uses_command_file_path_for_flammap(tmp_path, monkeypatch):
    fb_root = tmp_path / "FB"
    sample_dir = fb_root / "sampledata" / "FlamMap"
    sample_dir.mkdir(parents=True)
    cmd_file = sample_dir / "FlamMapCommand.txt"
    cmd_file.write_text("dummy")
    monkeypatch.setattr(fm, "fb_path", str(fb_root))
    captured = {}
    monkeypatch.setattr(
        fm,
        "run_app",
        lambda app_select, command_file_path, **kwargs: captured.update(
            args=command_file_path
        ),
    )

    fm.app_test("FlamMap")

    assert isinstance(captured["args"], str)
    assert os.path.normpath(captured["args"]) == os.path.normpath(str(cmd_file))


def test_gen_randig_input_file_writes_vendor_sections(tmp_path):
    path = fm.gen_randig_input_file(
        str(tmp_path),
        "randig",
        10,
        720,
        0.2,
        minimum_number_fires=10,
        mtt_spot_delay=0,
        fuel_moisture_data=(1, "0 4 6 9 60 90"),
        gridded_winds_generate="Yes",
        gridded_winds_resolution=30,
        suppress_messages=True,
    )
    with open(path) as file:
        content = file.read()
    assert content.startswith("#Randig-Inputs-File-Version-1")
    assert "NUMFIRES: 10" in content
    assert "MTT_SPOT_DELAY: 0" in content
    assert "NUMBER_PROCESSORS" not in content
    assert "GRIDDED_WINDS_RESOLUTION: 30" in content


def test_gen_randig_input_file_rejects_invalid_controls(tmp_path):
    with pytest.raises(ValueError):
        fm.gen_randig_input_file(str(tmp_path), "bad", 0, 1, 0.2)
    with pytest.raises(ValueError):
        fm.gen_randig_input_file(str(tmp_path), "bad", 1, 1, 1.1)


def test_gen_fspro_input_file_writes_counts_and_sections(tmp_path):
    path = fm.gen_fspro_input_file(
        str(tmp_path),
        "fspro",
        1,
        1,
        30,
        9,
        1,
        [45, 90],
        [5],
        [[1.0, 2.0]],
        [[1, 2, 3, 4, 5, 6, 7, 8, 0.1, 0]],
        [[1, 2]],
        [1, 2],
        [0.1, 0.2],
        [1, 2],
        forecast=[[1, 2, 3]],
        suppress_messages=True,
    )
    with open(path) as file:
        content = file.read()
    assert content.startswith("#FSPro Model Inputs")
    assert "[B@" not in content
    assert "NumWindDirs: 2" in content
    assert "NumERCYears: 1" in content
    assert "NumForecast: 1" in content


def test_gen_fspro_input_file_rejects_bad_matrix_and_crown_method(tmp_path):
    args = (
        str(tmp_path),
        "bad",
        1,
        1,
        30,
        9,
        1,
        [45],
        [5],
        [[1]],
        [[1] * 10],
        [[1]],
        [1],
        [1],
        [1],
    )
    with pytest.raises(ValueError):
        fm.gen_fspro_input_file(*args, crown_fire_method="ScottReinhardt")
    with pytest.raises(ValueError):
        fm.gen_fspro_input_file(
            str(tmp_path),
            "bad",
            1,
            1,
            30,
            9,
            1,
            [45],
            [5],
            [[1, 2]],
            [[1] * 10],
            [[1]],
            [1],
            [1],
            [1],
        )
