"""Manual Farsite driver using repository fixtures; do not run in pytest or CI."""

import os

import pandas as pd

import flammap_cli as fm

TEST_DIR = os.path.dirname(__file__)
INPUT_DIR = os.path.join(TEST_DIR, "test_inputs")
IGNITION_PATH = os.path.join(TEST_DIR, "test_ignitions", "ignition_point.shp")
LCP_PATH = os.path.join(TEST_DIR, "test_lcps", "test_lcp.tif")
OUTPUT_DIR = os.path.join(TEST_DIR, "test_outputs", "farsite")


def create_lcp():
    if not os.path.exists(LCP_PATH):
        os.makedirs(os.path.dirname(LCP_PATH), exist_ok=True)
        names = ("Elevation", "Slope", "Aspect", "FBFM", "CC", "CH", "CBH", "CBD")
        fm.gen_lcp(
            LCP_PATH,
            *[
                os.path.join(INPUT_DIR, f"{name}_UTM_resampled30m.tif")
                for name in names
            ],
        )
    return LCP_PATH


def csv_data(name):
    values = (
        pd.read_csv(os.path.join(INPUT_DIR, name), header=0).astype(int).values.tolist()
    )
    return fm.gen_weather_string(values)


def create_input():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return fm.gen_flammap_input_file(
        out_dir=OUTPUT_DIR,
        out_name="farsite_input",
        app_select="Farsite",
        fuel_moisture_data=csv_data("fuel_moisture.csv"),
        raws_elev=205,
        raws_units="English",
        raws_data=csv_data("weather.csv"),
        wind_direction=45,
        wind_speed=4,
        wind_spd_units=0,
        foliar_mc=80,
        crown_fire_method="ScottReinhardt",
        far_start_time="07 14 1000",
        far_end_time="07 17 1800",
        far_timestep=60,
        far_dist_res=30,
        far_spot_prob=0,
        far_spot_ign_delay=0,
        far_min_spot_dist=60,
        far_accel_on=1,
        far_burn_periods=csv_data("burn_periods.csv"),
        far_fill_barriers=1,
    )


def run_farsite():
    input_path = create_input()
    command_path = os.path.join(OUTPUT_DIR, "farsite_command.txt")
    fm.gen_command_file(
        command_path,
        [
            [
                create_lcp(),
                input_path,
                IGNITION_PATH,
                0,
                os.path.join(OUTPUT_DIR, "farsite_output"),
                2,
            ]
        ],
    )
    return fm.run_app("Farsite", command_path)


if __name__ == "__main__":
    run_farsite()
