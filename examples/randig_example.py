"""Manual Randig driver using repository example landscape inputs; do not run in pytest or CI."""

import os

from flame_components import flammap_cli as fm

example_dir = os.path.dirname(__file__)
example_input_dir = os.path.join(example_dir, "example_inputs")
example_ignition_dir = os.path.join(example_dir, "example_ignitions")
example_lcp_dir = os.path.join(example_dir, "example_lcps")


def create_lcp():
    os.makedirs(example_lcp_dir, exist_ok=True)
    lcp_path = os.path.join(example_lcp_dir, "example_lcp.tif")
    if not os.path.exists(lcp_path):
        names = ["Elevation", "Slope", "Aspect", "FBFM", "CC", "CH", "CBH", "CBD"]
        fm.gen_lcp(
            lcp_path,
            *[
                os.path.join(example_input_dir, f"{name}_UTM_resampled30m.tif")
                for name in names
            ],
        )
    return lcp_path


def create_input():
    out_dir = os.path.join(example_dir, "example_outputs", "randig")
    os.makedirs(out_dir, exist_ok=True)
    return fm.gen_randig_input_file(
        out_dir=out_dir,
        out_name="randig_input",
        num_fires=10,
        duration=720,
        spot_probability=0.2,
        minimum_number_fires=10,
        mtt_spot_delay=0,
        fuel_moisture_data=(1, "0 4 6 9 60 90"),
        gridded_winds_generate="Yes",
        gridded_winds_resolution=30,
    )


def run_randig(input_path, lcp_path):
    out_dir = os.path.dirname(input_path)
    return fm.run_app(
        app_select="Randig",
        command_file_path=[
            lcp_path,
            input_path,
            os.path.join(out_dir, "randig_output"),
        ],
        cwd=out_dir,
    )


if __name__ == "__main__":
    run_randig(input_path=create_input(), lcp_path=create_lcp())
