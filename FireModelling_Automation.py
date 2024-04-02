# -*- coding: utf-8 -*-
"""
Created on Tue April 2 12:30:00 2024

@author: Gregory A. Greene
"""
__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import os
import subprocess
import rasterio as rio

fbx64_path = '.\\Supplementary_Data\\FB_x64\\'

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
        with open(inPath, 'r') as file:
            contents = file.read()
            lines = len(contents.split('\n'))
        file.close()
    except FileNotFoundError:
        print('The data directory does not exist')

    return lines, contents


def genCommandFile(outPath, commandOut):
    if os.path.exists(outPath):
        os.remove(outPath)

    try:
        file = open(outPath, 'w')
        for row in commandOut:
            file.write(f'{row[0]} {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}\n')
        file.close()
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def genFarsiteInputFile(outPath, modelBaseName, fuelMoistureData, weatherData, foliarMC=100, burnPeriods=1,
                        crownFireMethod='ScottReinhardt'):
    if os.path.exists(outPath):
        os.remove(outPath)

    # Change the following values for each model run
    try:
        file = open(outPath, 'w')
        file.write(
            f"""# FARSITE INPUT FILE FOR {modelBaseName}
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
FARSITE_BURN_PERIODS: {burnPeriods}
08 18 1200 1800
08 19 1200 1800

FUEL_MOISTURES_DATA: {fuelMoistureData[0]}
{fuelMoistureData[1]}
{weatherData[1]}

FOLIAR_MOISTURE_CONTENT: {foliarMC}
CROWN_FIRE_METHOD: {crownFireMethod}
"""
        )
        file.close()
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def genFlamMapInputFile(outPath, modelBaseName, fuel_cnd_end, fuelMoistureData,
                        raws_elev, raws_units, weatherData,
                        foliarMC=100, crownFireMethod='ScottReinhardt', numProcessors=1,
                        wnd_spd_units=0, wind_dir_path='', wind_spd_path=''
                        ):

    # Delete existing output file
    if os.path.exists(outPath):
        os.remove(outPath)

    # Change the following values for each model run
    try:
        file = open(outPath, 'w')
        file.write(
            f"""# FLAMMAP INPUT FILE FOR {modelBaseName}
FlamMap-Inputs-File-Version-1
CONDITIONING_PERIOD_END: {fuel_cnd_end}

FUEL_MOISTURES_DATA: {fuelMoistureData[0]}
{fuelMoistureData[1]}
RAWS_ELEVATION: {raws_elev}
RAWS_UNITS: {raws_units}

RAWS: {weatherData[0]}
{weatherData[1]}

FOLIAR_MOISTURE_CONTENT: {foliarMC}
CROWN_FIRE_METHOD: {crownFireMethod}
NUMBER_PROCESSORS: {numProcessors}
SPREAD_DIRECTION_FROM_MAX: 0
WIND_SPEED_UNITS: {wnd_spd_units}
GRIDDED_WINDS_DIRECTION_FILE: {wind_dir_path}
GRIDDED_WINDS_SPEED_FILE: {wind_spd_path}

CROWNSTATE:
INTENSITY:
SPREADRATE:
CROWNFRACTIONBURNED:
FLAMELENGTH:
MIDFLAME:
FUELMOISTURE1:
FUELMOISTURE10:
FUELMOISTURE100:
FUELMOISTURE1000:
"""
        )
        file.close()
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def genMTTInputFile(out_path, model_base_name, output_list, fuel_cnd_end, fuel_moisture_data,
                    raws_elev, raws_units, weather_data, foliar_mc=100, crown_fire_method='ScottReinhardt',
                    num_processors=1, spread_direction_from_max=0, wnd_spd_units=0, wind_dir_path='', wind_spd_path='',
                    mtt_resolution=100, mtt_sim_time=0, mtt_ravel_path_interval=500,
                    mtt_spot_probability=0, mtt_spot_delay=0, mtt_ignition_file_path=None,
                    mtt_barrier_file=0, mtt_fill_barriers=1, node_spread_num_lat=6, node_spread_num_vert=4,
                    TREAT_RESOLUTION=None, TREAT_IGNITION_FILE=None, TREAT_IDEAL_LANDSCAPE=None,
                    TREAT_ITERATIONS=None, TREAT_DIMENSION=None, TREAT_FRACTION=None, TREAT_OPPORTUNITIES_ONLY=None
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
WIND_SPEED_UNITS: {wnd_spd_units}
GRIDDED_WINDS_DIRECTION_FILE: {wind_dir_path}
GRIDDED_WINDS_SPEED_FILE: {wind_spd_path}

MTT_RESOLUTION: {mtt_resolution}
MTT_SIM_TIME: {mtt_sim_time}
MTT_TRAVEL_PATH_INTERVAL: {mtt_ravel_path_interval}
MTT_SPOT_PROBABILITY: {mtt_spot_probability}
MTT_SPOT_DELAY: {mtt_spot_delay}
MTT_IGNITION_FILE: {mtt_ignition_file_path}
MTT_BARRIER_FILE: {mtt_barrier_file}
MTT_FILL_BARRIERS: {mtt_fill_barriers}
NodeSpreadNumLat: {node_spread_num_lat}
NodeSpreadNumVert: {node_spread_num_vert}

        file = open(out_path, 'a')
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


def main():
    # ### GET PATHS TO DIRECTORIES AND FILES
    # Path to application executable file
    app_selection = 'MTT'
    # Path to modelling data folder
    #flammap_dataPath = '.\\Supplementary_Data\\Farsite_Data'
    data_path = r'E:\EastKootenayProject_FarsiteTesting'
    os.chdir(data_path)
    # Path to input burn period data
    burnPeriod_dataPath = None
    # Path to input fuel moisture data
    fuelMoisture_dataPath = r'E:\EastKootenayProject_FarsiteTesting\Koot_FM.fms'
    # Path to input weather dataset
    weather_dataPath = r'E:\EastKootenayProject_FarsiteTesting\TESTManualInput90.wxs'

    # ### FLAMMAP SWITCHES
    foliarMC = 100                      # Foliar Moisture Content
    burnPeriods = 2                     # Number of burn periods
    crownFireMethod = 'ScottReinhardt'  # Method to use for crown fire spread (ScottReinhardt, Finney)
    numProcessors = 6   # Number of processors to use for multiprocessing (for simultaneous fire simulations)

    # Name and path of Farsite landscape file
    lcp_file_name = 'WestKootenay_TestLCP.tif'
    #lcp_file_name = '69121.lcp'
    #lcp_file_path = os.path.join(farsite_dataPath, lcp_file_name)

    # Name and path of Farsite modelling input data file
    input_file_name = 'test12345.input'
    #input_file_name = '062913.input'
    input_file_path = os.path.join(data_path, input_file_name)

    # Name and path of Farsite modelling ignition file
    ignition_file_name = '50_Wkoot_ign.shp'
    #ignition_file_name = '69121_NTFBPerimeter.shp'
    #ignition_file_path = os.path.join(farsite_dataPath, ignition_file_name)

    # Name and path of Farsite modelling output data
    outBaseName = 'MTT_Test'
    outPath = os.path.join(data_path, 'Outputs', outBaseName)

    # List of desired output parameters
    output_list = ['CROWNSTATE', 'INTENSITY', 'SPREADRATE', 'CROWNFRACTIONBURNED', 'FLAMELENGTH',
                   'MIDFLAME', 'FUELMOISTURE1', 'FUELMOISTURE10', 'FUELMOISTURE100', 'FUELMOISTURE1000']


    # ### SET UP COMMAND FILE PARAMETERS (ALL 6 REQUIRED)
    # Command file name and path
    command_file_name = 'FlamMapTestCmd.txt'
    command_file_path = os.path.join(data_path, command_file_name)
    # Command file input parameters
    lcpFile = lcp_file_name                     # Name of landscape file
    inputFile = input_file_name                 # Name of input file
    ignitionFile = ignition_file_name           # Name of ignition shapefile
    barrierFile = 0                             # Name of barrier shapefile format; 0 if no barrier
    outFolder = outPath                         # Path to output folder, and base name of file
    outType = 2                                 # File type for outputs; 0 = both, 1 = ASCII grid, 2 = GeoTIFF

    # Get LCP raster resolution
    lcpras = rio.open(lcpFile)
    lcpResolution = lcpras.affine[0]
    del lcpras

    # ### GENERATE FARSITE MODELLING DATASETS
    # Get burn period data
    #burnPeriodData = getText(burnPeriod_dataPath)
    burnPeriodData = None
    # Get fuel moisture data
    fuelMoistureData = getText(fuelMoisture_dataPath)
    # Get weather data
    weatherData = getText(weather_dataPath)
    # Generate input file
    genMTTInputFile(out_path=input_file_path, model_base_name=outBaseName, output_list=output_list,
                    fuel_cnd_end=None, fuel_moisture_data=fuelMoistureData,
                    raws_elev=, raws_units=,
                    weather_data=weatherData, foliar_mc=foliarMC,
                    crown_fire_method=crownFireMethod, num_processors=numProcessors,
                    spread_direction_from_max=0, wnd_spd_units=0, wind_dir_path='', wind_spd_path='',
                    mtt_resolution=lcpResolution, mtt_ignition_file_path='',
                    )
    # Generate command file (THIS COULD BE WRITTEN TO INCLUDE MULTIPLE INPUT FILES)
    commandOut = [[lcpFile, inputFile, ignitionFile, barrierFile, outFolder, outType]]
    genCommandFile(command_file_path, commandOut)

    app_exe_path = os.path.join(app_exe_dict.get(app_selection, None), 'bin')
    app_testData_path = os.path.join(app_testData_dict.get(app_selection, None), 'SampleData')


    ### RUN MODELLING
    print(f'Running {app_selection} modelling...')
    mttCLI = subprocess.run(
        [f'{app_exe_path}', command_file_path],
        capture_output=True,
        text=True
    )
    print(f'\n{mttCLI.stdout}')
    print('\nFarsite modelling complete')


if __name__ == '__main__':

    main()
