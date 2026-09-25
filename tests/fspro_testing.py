"""Manual FSPro driver using repository landscape and ignition inputs; do not run in pytest or CI."""

import os

import flammap_cli as fm

test_dir = os.path.dirname(__file__)
input_dir = os.path.join(test_dir, "test_inputs")
ign_dir = os.path.join(test_dir, "test_ignitions")
lcp_dir = os.path.join(test_dir, "test_lcps")


def create_lcp():
    os.makedirs(lcp_dir, exist_ok=True)
    lcp_path = os.path.join(lcp_dir, "test_lcp.tif")
    if not os.path.exists(lcp_path):
        names = ["Elevation", "Slope", "Aspect", "FBFM", "CC", "CH", "CBH", "CBD"]
        fm.gen_lcp(
            lcp_path,
            *[
                os.path.join(input_dir, f"{name}_UTM_resampled30m.tif")
                for name in names
            ],
        )
    return lcp_path


def create_input():
    out_dir = os.path.join(test_dir, "test_outputs", "fspro")
    os.makedirs(out_dir, exist_ok=True)
    return fm.gen_fspro_input_file(
        out_dir,
        "fspro_input",
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
    )


def run_fspro(input_path, lcp_path):
    out_dir = os.path.dirname(input_path)
    ignition = os.path.join(ign_dir, "ignition_point.shp")
    return fm.run_app(
        "FSPro",
        [lcp_path, input_path, os.path.join(out_dir, "fspro_output"), ignition, "0"],
        cwd=out_dir,
    )


if __name__ == "__main__":
    run_fspro(create_input(), create_lcp())
