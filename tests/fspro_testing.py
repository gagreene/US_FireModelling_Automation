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
        out_dir=out_dir,
        out_name="fspro_input",
        duration=1,
        num_fires=1,
        max_lag=30,
        poly_degree=9,
        calm_value=1,
        wind_directions=[45, 90],
        wind_speeds=[5],
        wind_cell_values=[[1.0, 2.0]],
        erc_classes=[[1, 2, 3, 4, 5, 6, 7, 8, 0.1, 0]],
        historic_erc_values=[[1, 2]],
        avg_erc_values=[1, 2],
        stddev_erc_values=[0.1, 0.2],
        current_erc_values=[1, 2],
    )


def run_fspro(input_path, lcp_path):
    out_dir = os.path.dirname(input_path)
    ignition = os.path.join(ign_dir, "ignition_point.shp")
    return fm.run_app(
        app_select="FSPro",
        command_file_path=[
            lcp_path,
            input_path,
            os.path.join(out_dir, "fspro_output"),
            ignition,
            "0",
        ],
        cwd=out_dir,
    )


if __name__ == "__main__":
    run_fspro(input_path=create_input(), lcp_path=create_lcp())
