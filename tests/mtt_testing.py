# -*- coding: utf-8 -*-
"""
Created on Sat Nov 29 12:30:00 2025

@author: Gregory A. Greene
"""
__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import os
import pandas as pd
import flammap_cli as fm

# Get paths to data/processing directories
test_dir = os.path.dirname(__file__)
input_dir = os.path.join(test_dir, 'test_inputs')
ign_dir = os.path.join(test_dir, 'test_ignitions')
lcp_dir = os.path.join(test_dir, 'test_lcps')
out_dir = os.path.join(test_dir, 'test_outputs', 'mtt')
os.makedirs(lcp_dir, exist_ok=True)
os.makedirs(out_dir, exist_ok=True)

# Create path to output LCP file
lcp_path = os.path.join(lcp_dir, 'test_lcp.tif')

# Get ignition file path
ign_path = os.path.join(ign_dir, 'ignition_point.shp')
# ign_path = os.path.join(ign_dir, '69121_NTFBPerimeter_UTM.shp')

# Set app selection
app_selection = 'MTT'

# Settings and switches
raws_elev = 205  # Elevation of RAWs station (meters)
raws_units = 'English'  # Units of RAWs data (English or Metric)
wind_speed_units = 0  # Units of wind speed data (0 = mph, 1 = kph, 3 = m/s, 4 = ft/min)
wind_direction = 45  # Wind direction value
wind_speed = 4  # Wind speed value
foliar_mc = 80  # Foliar moisture content (%)
model_resolution = 30  # Modelling resolution
crown_fire_method = 'ScottReinhardt'  # Method to use for crown fire spread (ScottReinhardt, Finney)
sim_time = 240  # Simulation time (simulated minutes)
travel_path_interval = 240  # Travel path interval (meters)
spot_probability = 0  # Spot probability (proportion, range 0-1)
spot_delay = 0  # Spot delay time (minutes)
node_spread_num_lat = 6  # Number of nodes to spread laterally (default = 6)
node_spread_num_vert = 4  # Number of nodes to spread vertically (default = 4)


def get_csv_as_df(csv_path):
    return pd.read_csv(csv_path, header=0, index_col=False)


def create_lcp():
    # Get paths to LCP input datasets
    data_names = ['Elevation', 'Slope', 'Aspect', 'FBFM', 'CC', 'CH', 'CBH', 'CBD']
    lcp_input_paths = [lcp_path]
    for name in data_names:
        lcp_input_paths.append(os.path.join(input_dir, f'{name}_UTM_resampled30m.tif'))

    # Generate LCP file
    fm.genLCP(*lcp_input_paths)
    return


def create_input():
    # Get burn period data
    bp_csv = os.path.join(input_dir, 'burn_periods.csv')
    bp_df = get_csv_as_df(bp_csv)
    # Format burn period data for genInputFile() function
    bp_data = fm.genWeatherString(bp_df.astype(int).values.tolist())

    # Get fuel moisture data
    fmoist_csv = os.path.join(input_dir, 'fuel_moisture.csv')
    fmoist_df = get_csv_as_df(fmoist_csv)
    # Format fuel moisture data for genInputFile() function
    fmoist_data = fm.genWeatherString(fmoist_df.astype(int).values.tolist())

    # Get weather data
    wx_csv = os.path.join(input_dir, 'weather.csv')
    wx_df = get_csv_as_df(wx_csv)
    # Format weather data for genInputFile() function
    raws_data = fm.genWeatherString(wx_df.astype(int).values.tolist())

    # Generate the input file
    input_path = fm.genInputFile(
        out_dir=out_dir,
        out_name='farsite_testing_input',
        suppress_messages=False,
        app_select=app_selection,
        fuel_moisture_data=fmoist_data,
        raws_elev=raws_elev,
        raws_units=raws_units,
        raws_data=raws_data,
        wind_direction=wind_direction,
        wind_speed=wind_speed,
        wind_spd_units=wind_speed_units,
        foliar_mc=foliar_mc,
        crown_fire_method=crown_fire_method,
        mtt_node_spread_num_lat=node_spread_num_lat,
        mtt_node_spread_num_vert=node_spread_num_vert,
        mtt_resolution=model_resolution,
        mtt_sim_time=sim_time,
        mtt_travel_path_interval=travel_path_interval,
        mtt_spot_probability=spot_probability,
        mtt_spot_delay=spot_delay,
        mtt_ign_file_path=ign_path
    )
    return input_path


def create_command(input_path, command_path):
    # Create command file data list
    mtt_out_path = os.path.join(out_dir, 'mtt_testing_output')
    command_list = [
        [lcp_path, input_path, ign_path, 0, mtt_out_path, 2]
    ]

    # Generate command file
    fm.genCommandFile(
        out_path=command_path,
        command_list=command_list,
        suppress_messages=False
    )
    return


def run_mtt(command_path):
    # Run MTT
    fm.runApp(
        app_select=app_selection,
        command_file_path=command_path,
        suppress_messages=False
    )
    return


if __name__ == '__main__':
    if not os.path.exists(lcp_path):
        # Create the LCP file
        create_lcp()

    # Generate Input file
    input_file = create_input()

    # Generate Command file
    command_file = os.path.join(out_dir, 'mtt_testing_command.txt')
    create_command(input_path=input_file, command_path=command_file)

    # Run MTT
    run_mtt(command_path=command_file)
