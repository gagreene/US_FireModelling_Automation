# -*- coding: utf-8 -*-
"""
Created on Tue April 2 12:30:00 2024

@author: Gregory A. Greene
"""
__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import os
import subprocess
import rasterio as rio

fbx64_path = os.path.join(os.path.dirname(__file__), r'Supplementary_Data\FB_x64')

app_exe_dict = {
    'FlamMap': os.path.join(fbx64_path, 'bin\\TestFlamMap'),
    'MTT': os.path.join(fbx64_path, 'bin\\TestMTT'),
    'Farsite': os.path.join(fbx64_path, 'bin\\TestFARSITE'),
    'FSPro': os.path.join(fbx64_path, 'bin\\TestFSPro'),
    'SpatialFOFEM': os.path.join(fbx64_path, 'bin\\TestSpatialFOFEM')
}

app_testData_dict = {
    'FlamMap': os.path.join(fbx64_path, 'TestFlamMap\\SampleData'),
    'MTT': os.path.join(fbx64_path, 'TestMTT\\SampleData'),
    'Farsite': os.path.join(fbx64_path, 'TestFARSITE\\SampleData'),
    'FSPro': os.path.join(fbx64_path, 'TestFSPro\\SampleData'),
    'SpatialFOFEM': os.path.join(fbx64_path, 'TestSpatialFOFEM\\SampleData')
}


def getText(inPath):
    lines = None
    contents = None
    try:
        with open(inPath, 'r') as reader:
            data = reader.read().rstrip('\n')
        with open(inPath, 'w') as writer:
            zero_line = data.split('\n')[0]
            first_fbfm = zero_line.split(' ')[0]
            zero_line = zero_line.replace(first_fbfm, '0', 1)
            writer.write(f'{zero_line}\n{data}')
        with open(inPath, 'r') as file:
            contents = file.read()
            #contents.replace('\n\n', '\n')
            lines = len(contents.split('\n'))
    except FileNotFoundError:
        print('The data directory does not exist')

    return lines, contents


def genCommandFile(out_path, commandOut):
    if os.path.exists(out_path):
        os.remove(out_path)

    try:
        file = open(out_path, 'w')
        for row in commandOut:
            file.write(f'{row[0]} {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}\n')
        file.close()
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def genFarsiteInputFile(out_path, model_base_name, fuel_moisture_data, weather_data, foliar_mc=100, burn_periods=1,
                        crown_fire_method='ScottReinhardt'):
    if os.path.exists(out_path):
        os.remove(out_path)

    # Change the following values for each model run
    try:
        file = open(out_path, 'w')
        file.write(
            f"""# FARSITE INPUT FILE FOR {model_base_name}
FARSITE INPUTS FILE VERSION 1.0
FARSITE_START_TIME: 08 15 0000
FARSITE_END_TIME: 08 19 2300
FARSITE_TIMESTEP: 60
FARSITE_DISTANCE_RES: 10.0
FARSITE_PERIMETER_RES: 60.0
FARSITE_MIN_IGNITION_VERTEX_DISTANCE: 15.0
FARSITE_SPOT_GRID_RESOLUTION: 5.0
FARSITE_SPOT_PROBABILITY: 0
FARSITE_SPOT_IGNITION_DELAY: 0
FARSITE_MINIMUM_SPOT_DISTANCE: 10
FARSITE_ACCELERATION_ON: 1
FARSITE_FILL_BARRIERS: 1
SPOTTING_SEED: 219490
FARSITE_BURN_PERIODS: {burn_periods}
08 18 1200 1800
08 19 1200 1800

FUEL_MOISTURES_DATA: {fuel_moisture_data[0]}
{fuel_moisture_data[1]}
{weather_data[1]}

FOLIAR_MOISTURE_CONTENT: {foliar_mc}
CROWN_FIRE_METHOD: {crown_fire_method}
"""
        )
        file.close()
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def genFlamMapInputFile(out_path, model_base_name, output_list, fuel_cnd_end, fuel_moisture_data,
                        raws_elev, raws_units, weather_data, foliar_mc=100, crown_fire_method='ScottReinhardt',
                        num_processors=1, spread_direction_from_max=0,
                        wind_speed_units=1, wind_dir_path='', wind_spd_path=''
                        ):

    # Delete existing output file
    if os.path.exists(out_path):
        os.remove(out_path)

    # Change the following values for each model run
    try:
        with open(out_path, 'w') as file:
            file.write(
                f"""# FLAMMAP INPUT FILE FOR {model_base_name}
FlamMap-Inputs-File-Version-1
CONDITIONING_PERIOD_END: {fuel_cnd_end}

FUEL_MOISTURES_DATA: {fuel_moisture_data[0]}
{fuel_moisture_data[1]}
RAWS_ELEVATION: {raws_elev}
RAWS_UNITS: {raws_units}

RAWS: {weather_data[0]}
{weather_data[1]}

FOLIAR_MOISTURE_CONTENT: {foliar_mc}
CROWN_FIRE_METHOD: {crown_fire_method}
NUMBER_PROCESSORS: {num_processors}
SPREAD_DIRECTION_FROM_MAX: {spread_direction_from_max}
WIND_SPEED_UNITS: {wind_speed_units}
GRIDDED_WINDS_DIRECTION_FILE: {wind_dir_path}
GRIDDED_WINDS_SPEED_FILE: {wind_spd_path}

# REQUESTED OUTPUTS
"""
            )
            if output_list:
                for output in output_list:
                    file.write(f'{output}:')
            else:
                file.write("""CROWNSTATE:
INTENSITY:
SPREADRATE:
CROWNFRACTIONBURNED:
FLAMELENGTH:
"""
                           )
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def genMTTInputFile(
        out_path, model_base_name, output_list, fuel_moisture_data=None, custom_fuels_file=None, fuel_cnd_end=None,
        raws_elev=None, raws_units=None, raws_data=None, weather_data=None, weather_units=None,
        foliar_mc=100, crown_fire_method='ScottReinhardt', num_processors=1, spread_direction_from_max=None,
        wind_spd_path=None, wind_dir_path=None, wind_speed=0, wind_direction=0, wind_spd_units=0,
        mtt_resolution=100, mtt_sim_time=0, mtt_travel_path_interval=500,
        mtt_spot_probability=0, mtt_spot_delay=0, mtt_ignition_file_path=None,
        mtt_barrier_file=None, mtt_fill_barriers=None, node_spread_num_lat=6, node_spread_num_vert=4,
        TREAT_RESOLUTION=None, TREAT_IGNITION_FILE=None, TREAT_IDEAL_LANDSCAPE=None,
        TREAT_ITERATIONS=None, TREAT_DIMENSION=None, TREAT_FRACTION=None, TREAT_OPPORTUNITIES_ONLY=None
                    ):
    # Delete existing output file
    if os.path.exists(out_path):
        os.remove(out_path)

    # Change the following values for each model run
    try:
        with open(out_path, 'w') as file:
            file.write(f'#FLAMMAP INPUT FILE FOR {model_base_name}\n')
            file.write('FlamMap-Inputs-File-Version-1\n')
            if fuel_cnd_end:
                file.write(f'CONDITIONING_PERIOD_END: {fuel_cnd_end}\n')
            if fuel_moisture_data:
                file.write(f'FUEL_MOISTURES_DATA: {fuel_moisture_data[0]}\n')
                file.write(f'{fuel_moisture_data[1]}\n')
                file.write('\n')
            if custom_fuels_file:
                file.write(f'CUSTOM_FUELS_FILE: {custom_fuels_file}\n')
        with open(out_path, 'a') as file:
            if raws_elev:
                file.write(f'RAWS_ELEVATION: {raws_elev}\n')
            if raws_units:
                file.write(f'RAWS_UNITS: {raws_units}\n')
                file.write('\n')
            if raws_data:
                file.write(f'RAWS: {raws_data[0]}\n')
                file.write(f'{raws_data[1]}\n')
                file.write('\n')
            if weather_units:
                file.write(f'WEATHER_UNITS: {weather_units}\n')
            if weather_data:
                file.write(f'WEATHER_DATA: {weather_data[0]}\n')
                file.write(f'{weather_data[1]}\n')
                file.write('\n')
            if spread_direction_from_max:
                file.write(f'SPREAD_DIRECTION_FROM_MAX: {spread_direction_from_max}\n')
            if wind_spd_path:
                file.write(f'GRIDDED_WIND_SPEED_FILE: {wind_spd_path}\n')
            if wind_dir_path:
                file.write(f'GRIDDED_WINDS_DIRECTION_FILE: {wind_dir_path}\n')
            file.write(f'WIND_SPEED: {wind_speed}\n')
            file.write(f'WIND_DIRECTION: {wind_direction}\n')
            file.write(f'WIND_SPEED_UNITS: {wind_spd_units}\n')
            file.write(f'FOLIAR_MOISTURE_CONTENT: {foliar_mc}\n')
            file.write(f'CROWN_FIRE_METHOD: {crown_fire_method}\n')
            file.write(f'NUMBER_PROCESSORS: {num_processors}\n')
            file.write('\n')
            file.write(f'MTT_RESOLUTION: {mtt_resolution}\n')
            file.write(f'MTT_SIM_TIME: {mtt_sim_time}\n')
            file.write(f'MTT_TRAVEL_PATH_INTERVAL: {mtt_travel_path_interval}\n')
            file.write(f'MTT_SPOT_PROBABILITY: {mtt_spot_probability}\n')
            file.write(f'MTT_SPOT_DELAY: {mtt_spot_delay}\n')
            file.write(f'MTT_IGNITION_FILE: {mtt_ignition_file_path}\n')
            if mtt_barrier_file:
                file.write(f'MTT_BARRIER_FILE: {mtt_barrier_file}\n')
            if mtt_fill_barriers:
                file.write(f'MTT_FILL_BARRIERS: {mtt_fill_barriers}\n')
            file.write(f'NodeSpreadNumLat: {node_spread_num_lat}\n')
            file.write(f'NodeSpreadNumVert: {node_spread_num_vert}\n')
            file.write('\n')
            file.write('#REQUESTED OUTPUTS\n')
            if output_list:
                for output in output_list:
                    file.write(f'{output}:\n')
            else:
                file.write('INTENSITY:\n'
                           'SPREADRATE:\n'
                           'FLAMELENGTH:\n'
                           'MAXSPREADDIR:\n'
                           'MAXSPOT\n'
                           'ELLIPSEDIM_A:\n'
                           'ELLIPSEDIM_B:\n'
                           'ELLIPSEDIM_C:\n'
                           'MTT_ROS\n'
                           'MTT_ARRIVAL\n'
                           'MTT_INTENSITY\n'
                           'MTT_FLOWPATHS:\n'
                           'MTT_CONTOUR\n')
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def runModel(app_selection, command_file_path):
    # ### RUN MODELLING
    print(f'<<<<< Running {app_selection} >>>>>')
    os.chdir(os.path.dirname(__file__) + r'\Supplementary_Data\FB_x64\bin')
    app_cli = subprocess.run(
        ['TestMTT', command_file_path],
        capture_output=True,
        text=True
    )
    print(f'{app_cli}')
    print(f'<<<<< {app_selection} modelling complete >>>>>')


if __name__ == '__main__':
    # Choose app to test
    app_selection = 'MTT'

    # ### GET PATHS TO DIRECTORIES AND FILES
    # Path to modelling data folder
    # flammap_dataPath = '.\\Supplementary_Data\\Farsite_Data'
    data_path = r'E:\EastKootenayProject_FarsiteTesting'
    os.chdir(data_path)
    # Path to input burn period data
    burnPeriod_dataPath = None
    # Path to input fuel moisture data
    fuelMoisture_dataPath = r'E:\EastKootenayProject_FarsiteTesting\Koot_FM.fms'
    # Path to input weather dataset
    weather_dataPath = r'E:\EastKootenayProject_FarsiteTesting\TESTManualInput90.wxs'

    # ### FLAMMAP SWITCHES
    foliar_mc = 100  # Foliar Moisture Content
    burn_periods = 2  # Number of burn periods
    crown_fire_method = 'ScottReinhardt'  # Method to use for crown fire spread (ScottReinhardt, Finney)
    num_processors = 6  # Number of processors to use for multiprocessing (for simultaneous fire simulations)

    # Name and path of Farsite landscape file
    lcp_file_name = 'WestKootenay_TestLCP.tif'
    # lcp_file_name = '69121.lcp'
    # lcp_file_path = os.path.join(farsite_dataPath, lcp_file_name)

    # Name and path of Farsite modelling input data file
    input_file_name = 'test12345.input'
    # input_file_name = '062913.input'
    input_file_path = os.path.join(data_path, input_file_name)

    # Name and path of Farsite modelling ignition file
    ignition_file_name = '50_Wkoot_ign.shp'
    # ignition_file_name = '69121_NTFBPerimeter.shp'
    # ignition_file_path = os.path.join(farsite_dataPath, ignition_file_name)

    # Name and path of Farsite modelling output data
    outBaseName = 'MTT_Test'
    out_path = os.path.join(data_path, 'Outputs', outBaseName)

    # List of desired output parameters
    output_list = ['CROWNSTATE', 'INTENSITY', 'SPREADRATE', 'CROWNFRACTIONBURNED', 'FLAMELENGTH',
                   'MIDFLAME', 'FUELMOISTURE1', 'FUELMOISTURE10', 'FUELMOISTURE100', 'FUELMOISTURE1000']

    # ### SET UP COMMAND FILE PARAMETERS (ALL 6 REQUIRED)
    # Command file name and path
    command_file_name = 'FlamMapTestCmd.txt'
    command_file_path = os.path.join(data_path, command_file_name)
    # Command file input parameters
    lcpFile = lcp_file_name  # Name of landscape file
    inputFile = input_file_name  # Name of input file
    ignitionFile = ignition_file_name  # Name of ignition shapefile
    barrierFile = 0  # Name of barrier shapefile format; 0 if no barrier
    outFolder = out_path  # Path to output folder, and base name of file
    outType = 2  # File type for outputs; 0 = both, 1 = ASCII grid, 2 = GeoTIFF

    # Get LCP raster resolution
    lcpras = rio.open(lcpFile)
    lcpResolution = lcpras.affine[0]
    del lcpras

    # ### GENERATE MTT MODELLING DATASETS
    # Get fuel moisture data
    fuel_moisture_data = getText(fuelMoisture_dataPath)
    # Get weather data
    weather_data = getText(weather_dataPath)
    # Generate input file
    # genMTTInputFile(out_path=input_file_path, model_base_name=outBaseName, output_list=output_list,
    #                 fuel_cnd_end=None, fuel_moisture_data=fuel_moisture_data,
    #                 raws_elev=, raws_units=,
    #                 weather_data=weather_data, foliar_mc=foliar_mc,
    #                 crown_fire_method=crown_fire_method, num_processors=num_processors,
    #                 spread_direction_from_max=0, wnd_spd_units=0, wind_dir_path='', wind_spd_path='',
    #                 mtt_resolution=lcpResolution, mtt_ignition_file_path='',
    #                 )
    # Generate command file (THIS COULD BE WRITTEN TO INCLUDE MULTIPLE INPUT FILES)
    commandOut = [[lcpFile, inputFile, ignitionFile, barrierFile, outFolder, outType]]
    genCommandFile(command_file_path, commandOut)

    app_testData_path = os.path.join(app_testData_dict.get(app_selection, None), 'SampleData')

    runModel(app_selection, command_file_path)
