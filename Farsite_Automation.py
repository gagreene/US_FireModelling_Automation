__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import os
import subprocess


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


def main():
    # ### GET PATHS TO DIRECTORIES AND FILES
    # Path to TestFARSITE executable file
    farsite_exePath = '.\\Supplementary_Data\\FB_x64\\bin\\TestFARSITE'
    # Path to farsite modelling data folder
    #farsite_dataPath = '.\\Supplementary_Data\\Farsite_Data'
    farsite_dataPath = r'E:\EastKootenayProject_FarsiteTesting'
    os.chdir(farsite_dataPath)
    # Path to input burn period data
    burnPeriod_dataPath = None
    # Path to input fuel moisture data
    fuelMoisture_dataPath = r'E:\EastKootenayProject_FarsiteTesting\Koot_FM.fms'
    # Path to input weather dataset
    weather_dataPath = r'E:\EastKootenayProject_FarsiteTesting\TESTManualInput90.wxs'

    # ### FARSITE SWITCHES
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
    input_file_path = os.path.join(farsite_dataPath, input_file_name)

    # Name and path of Farsite modelling ignition file
    ignition_file_name = '50_Wkoot_ign.shp'
    #ignition_file_name = '69121_NTFBPerimeter.shp'
    #ignition_file_path = os.path.join(farsite_dataPath, ignition_file_name)

    # Name and path of Farsite modelling output data
    outBaseName = 'FarsiteTest'
    outPath = os.path.join(farsite_dataPath, 'Outputs', outBaseName)


    # ### SET UP COMMAND FILE PARAMETERS (ALL 6 REQUIRED)
    # Command file name and path
    command_file_name = 'FarsiteTestCmd.txt'
    command_file_path = os.path.join(farsite_dataPath, command_file_name)
    # Command file input parameters
    lcpFile = lcp_file_name                     # Name of landscape file
    inputFile = input_file_name                 # Name of input file
    ignitionFile = ignition_file_name           # Name of ignition shapefile
    barrierFile = 0                             # Name of barrier shapefile format; 0 if no barrier
    outFolder = outPath                         # Path to output folder, and base name of file
    outType = 2                                 # File type for outputs; 0 = both, 1 = ASCII grid, 2= GeoTIFF


    # ### GENERATE FARSITE MODELLING DATASETS
    # Get burn period data
    #burnPeriodData = getText(burnPeriod_dataPath)
    burnPeriodData = None
    # Get fuel moisture data
    fuelMoistureData = getText(fuelMoisture_dataPath)
    # Get weather data
    weatherData = getText(weather_dataPath)
    # Generate input file
    genFarsiteInputFile(outPath=input_file_path, modelBaseName=outBaseName, fuelMoistureData=fuelMoistureData,
                        weatherData=weatherData, foliarMC=foliarMC,
                        burnPeriods=burnPeriods, crownFireMethod=crownFireMethod, numProcessors=numProcessors)
    # Generate command file (THIS COULD BE WRITTEN TO INCLUDE MULTIPLE INPUT FILES)
    commandOut = [[lcpFile, inputFile, ignitionFile, barrierFile, outFolder, outType]]
    genCommandFile(command_file_path, commandOut)


    ### RUN FARSITE MODELLING
    print('Running Farsite modelling...')
    farsiteCon = subprocess.run(
        [f'{farsite_exePath}', command_file_path],
        capture_output=True,
        text=True
    )
    print(f'\n{farsiteCon.stdout}')
    print('\nFarsite modelling complete')


if __name__ == '__main__':
    main()
