# -*- coding: utf-8 -*-
"""
Created on Tue April 2 12:30:00 2024

@author: Gregory A. Greene
"""
__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import os
import glob
import subprocess
import psutil
import rasterio as rio
from numpy import histogram
from numpy.ma import masked_equal
from typing import Union, Optional

supplementary_path = os.path.join(os.path.dirname(__file__), 'supplementary_data')
fb_path = os.path.join(supplementary_path, 'FB')
bin_path = os.path.join(fb_path, 'bin')

app_name_dict = {
    'FlamMap': 'TestFlamMap',
    'MTT': 'TestMTT',
    'TOM': 'TestMTT',
    'Farsite': 'TestFARSITE',
    # 'FSPro': 'TestFSPro',
    # 'SpatialFOFEM': 'TestSpatialFOFEM'
}

app_exe_dict = {
    'FlamMap': os.path.join(bin_path, 'TestFlamMap'),
    'MTT': os.path.join(bin_path, 'TestMTT'),
    'TOM': os.path.join(bin_path, 'TestMTT'),
    'Farsite': os.path.join(bin_path, 'TestFARSITE'),
    'FSPro': os.path.join(bin_path, 'TestFSPro'),
    'SpatialFOFEM': os.path.join(bin_path, 'TestSpatialFOFEM')
}


def downloadApps() -> None:
    import requests
    import shutil
    import zipfile

    # The URL of the zip file
    data_url = 'https://www.alturassolutions.com/FB/FB.zip'

    # Ensure the supplementary folder exists
    os.makedirs(supplementary_path, exist_ok=True)

    # Send an HTTP GET request to the URL
    print(f'Downloading FB data')
    response = requests.get(data_url, stream=True)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Path to save the downloaded zip file
        zip_file_path = os.path.join(supplementary_path, 'FB.zip')

        # Open a local file in binary write mode and save the downloaded content
        with open(zip_file_path, 'wb') as file:
            shutil.copyfileobj(response.raw, file)

        print(f'Download complete: {zip_file_path}')

        # Extract the zip file to the supplementary folder
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(supplementary_path)

        print(f'Extraction complete: {supplementary_path}')

        # Delete the zip file after extraction
        os.remove(zip_file_path)
        print(f'Zip file removed: {zip_file_path}')
    else:
        print(f'Failed to download file: {response.status_code}')

    return


def genLCP(lcp_file: str,
           elev_path: str,
           slope_path: str,
           aspect_path: str,
           fbfm_path: str,
           cc_path: str,
           ch_path: str,
           cbh_path: str,
           cbd_path: str) -> None:
    """
    Generate a compressed, tiled, multiband GeoTIFF file suitable for use as a Landscape (LCP) file,
    by stacking 8 raster tif file inputs. Results are not as compressed as the genLCP_gdal function.

    :param lcp_file: path to output lcp file
    :param elev_path: path to elevation dataset
    :param slope_path: path to slope dataset (degrees)
    :param aspect_path: path to aspect dataset (degrees)
    :param fbfm_path: path to fire behavior fuel model (FBFM) dataset
    :param cc_path: path to canopy cover dataset
    :param ch_path: path to canopy height dataset
    :param cbh_path: path to canopy base height (CBH) dataset
    :param cbd_path: path to canopy bulk density (CBD) dataset
    :return: None
    """
    print(f'Generating LCP file at {lcp_file}')

    # Generate raster and band names lists
    rasters = [elev_path, slope_path, aspect_path, fbfm_path, cc_path, ch_path, cbh_path, cbd_path]
    band_names = ['elev', 'slope', 'aspect', 'fbfm', 'cnpy_cvr', 'cnpy_ht', 'cbh', 'cbd']

    # Read metadata from the reference raster
    with rio.open(elev_path) as ref_ras:
        ref_shape = ref_ras.shape
        out_meta = ref_ras.meta.copy()

    # Update metadata for the output GeoTIFF
    out_meta.update({
        'count': 8,         # 8 output bands
        'dtype': 'int16',   # 16-bit integer format
        'nodata': -999,     # Nodata value for all bands
        'compress': 'DEFLATE',  # Compression method
        'zlevel': 9,        # Compression level (0-9)
        'predictor': 2,     # Improve compression for continuous data
        'tiled': True,      # Enable tiling for efficient access
        'blockxsize': 128,  # Tile width
        'blockysize': 128,  # Tile height
        'BIGTIFF': 'YES'    # Support >4GB output files
    })

    # Write data to output LCP file
    print('\tSaving LCP file')
    with rio.open(lcp_file, 'w', **out_meta) as dst:
        # Loop through each input raster and corresponding band name
        for band, (path, desc) in enumerate(zip(rasters, band_names), start=1):
            with rio.open(path) as src:
                # Read and convert to int16 to match output dtype
                arr = src.read(1).astype('int16')

                # Replace input nodata values with unified -999
                nodata_value = src.nodata
                if nodata_value is not None:
                    arr[arr == nodata_value] = -999

                # Check shape consistency with the reference raster
                if arr.shape != ref_shape:
                    raise ValueError(f'Raster size mismatch in {path}. Expected {ref_shape}, got {arr.shape}')

                # Write the current band to the output file
                dst.write(arr, band)

                # Set band description (e.g., 'elev', 'slope', ...)
                dst.set_band_description(band, desc)

                # Mask nodata values before computing statistics
                arr_masked = masked_equal(arr, -999)

                # Compute and write basic stats as band-level metadata
                stats = {
                    'min': float(arr_masked.min()),
                    'max': float(arr_masked.max()),
                    'mean': float(arr_masked.mean()),
                    'std': float(arr_masked.std())
                }
                dst.update_tags(band, **stats)

                # Compute histogram (256 bins) and store as comma-separated string
                hist, bin_edges = histogram(arr_masked.compressed(), bins=256)
                dst.update_tags(band, histogram=','.join(map(str, hist.tolist())))

        # Add overall description tag to the first band
        dst.update_tags(1, DESCRIPTIONS=','.join(band_names))

    print(f'\tLCP file complete')

    return


def genLCP_gdal(lcp_file: str,
                elev_path: str,
                slope_path: str,
                aspect_path: str,
                fbfm_path: str,
                cc_path: str,
                ch_path: str,
                cbh_path: str,
                cbd_path: str) -> None:
    """
    Generate a compressed, tiled, multiband GeoTIFF file suitable for use as a Landscape (LCP) file,
    by stacking 8 raster layers using GDAL's VRT (Virtual Raster) and Translate functions.

    This function mimics the output structure and compression (size) used by ArcGIS Pro when using the Composite Bands
    tool to export stacked rasters to multi-band TIFF format with LZW compression.

    :param lcp_file: path to output lcp file
    :param elev_path: path to elevation dataset
    :param slope_path: path to slope dataset (degrees)
    :param aspect_path: path to aspect dataset (degrees)
    :param fbfm_path: path to fire behavior fuel model (FBFM) dataset
    :param cc_path: path to canopy cover dataset
    :param ch_path: path to canopy height dataset
    :param cbh_path: path to canopy base height (CBH) dataset
    :param cbd_path: path to canopy bulk density (CBD) dataset
    :return: None
    """
    def _updateLCP_Bands(file_path: str):
        band_names = ['elev', 'slope', 'aspect', 'fbfm', 'cnpy_cvr', 'cnpy_ht', 'cbh', 'cbd']
        with rio.open(file_path, 'r+') as dst:
            # Ensure there are 8 bands before assigning descriptions
            if dst.count == 8:
                # Explicitly set band descriptions
                for i, desc in enumerate(band_names, start=1):
                    dst.set_band_description(i, desc)  # Use explicit method

                # Alternatively, try updating tags (some drivers may require this)
                dst.update_tags(1, DESCRIPTIONS=','.join(band_names))
            else:
                print(f'\t\tSkipping band name assignments: Expected 8 bands, found {dst.count}.')

    print(f'Generating LCP file at {lcp_file}')

    # Generate raster and band names lists
    rasters = [elev_path, slope_path, aspect_path, fbfm_path, cc_path, ch_path, cbh_path, cbd_path]

    # Make sure all input rasters exist
    for ras in rasters:
        if not os.path.exists(ras):
            raise FileNotFoundError(f'\tInput raster not found: {ras}')

    # Create temporary VRT path
    vrt_path = lcp_file.replace('.tif', '.vrt')

    print('\tCreating VRT from rasters...')
    vrt_cmd = [
                  'gdalbuildvrt',
                  '-separate',
                  vrt_path
              ] + rasters

    subprocess.run(vrt_cmd, check=True)

    print('\tTranslating VRT to compressed GeoTIFF...')
    translate_cmd = [
        'gdal_translate',
        '-of', 'GTiff',
        '-co', 'COMPRESS=LZW',
        '-co', 'TILED=YES',
        '-co', 'BLOCKXSIZE=128',
        '-co', 'BLOCKYSIZE=128',
        '-co', 'BIGTIFF=YES',
        '-ot', 'Int16',
        vrt_path,
        lcp_file
    ]

    subprocess.run(translate_cmd, check=True)

    # Clean up VRT
    if os.path.exists(vrt_path):
        os.remove(vrt_path)

    # Update the band names in the LCP file
    print('\tUpdating LCP file band names...')
    _updateLCP_Bands(lcp_file)

    print(f'\tLCP file complete')

    return


def getRawsTextFile(in_path: str) -> tuple[int, str]:
    """
    Extracts contents from a text file containing RAWS-formatted weather data, and
    returns a tuple containing the length of the data, and a string representation of the data.

    :param in_path: Path to the text file.
    :return: Number of lines, and a formatted string containing the contents of the text file.
    """
    lines = None
    contents = None
    try:
        with open(in_path, 'r') as reader:
            data = reader.read().rstrip('\n')
        with open(in_path, 'w') as writer:
            zero_line = data.split('\n')[0]
            first_fbfm = zero_line.split(' ')[0]
            zero_line = zero_line.replace(first_fbfm, '0', 1)
            writer.write(f'{zero_line}\n{data}')
        with open(in_path, 'r') as file:
            contents = file.read()
            # contents.replace('\n\n', '\n')
            lines = len(contents.split('\n'))
    except FileNotFoundError:
        print('The data directory does not exist')

    return lines, contents


def genWeatherString(weather_list: list[list]) -> tuple[int, str]:
    """
    Converts a list of lists of properly formatted weather data, and returns a tuple containing the
    length of the list, and a string representation of the data.
    This function is intended to be used if passing data from a Pandas DataFrame or array that has been
    converted to a list of lists. Do not include column names, only the data.

    :param weather_list: A list of lists containing properly formatted weather data.
    :return: A tuple with the length of the list and the formatted string.
    """
    if not all(isinstance(sublist, list) for sublist in weather_list):
        raise ValueError('Input must be a list of lists.')

    list_length = len(weather_list)
    formatted_string = '\n'.join(' '.join(map(str, sublist)) for sublist in sorted(weather_list))

    return list_length, formatted_string


def genCommandFile(out_path: str,
                   command_list:  list[list[Union[str, int]]],
                   suppress_messages: bool = False) -> None:
    """
    Function to generate a command file
    :param out_path: path to save the output command file
    :param command_list: list of lists that contain the command file data
    :param suppress_messages: if True, do not print messages from this function
    :return: None
    """
    if not suppress_messages:
        print('\n<<<<< [flammap_cli.py] Generating Command File >>>>>')
    if os.path.exists(out_path):
        os.remove(out_path)

    try:
        file = open(out_path, 'w')
        for row in command_list:
            file.write(' '.join(map(str, row)) + '\n')
        file.close()
        if not suppress_messages:
            print('Command file complete')
    except FileNotFoundError:
        print('The command file directory does not exist')

    return


def genInputFile(
        out_dir: str,
        out_name: str,
        suppress_messages: bool = False,
        app_select: str = 'FlamMap',
        output_list: Optional[list] = None,
        cond_period_end: Optional[str] = None,
        fuel_moisture_data: Optional[Union[list[int, str], tuple[int, str]]] = None,
        custom_fuels_file: Optional[str] = None,
        raws_units: Optional[str] = None,
        raws_elev: Union[int, float] = None,
        raws_data: Optional[Union[list[int, str], tuple[int, str]]] = None,
        weather_data_units: Optional[str] = None,
        weather_data: Optional[list[int, str]] = None,
        wind_data_units: Optional[str] = None,
        wind_data: Optional[list[int, str]] = None,
        spread_direction_from_north: Optional[str] = None,
        spread_direction_from_max: Optional[str] = None,
        gridded_wind_spd_file: Optional[str] = None,
        gridded_wind_dir_file: Optional[str] = None,
        gridded_wind_gen: Optional[str] = None,
        gridded_wind_res: Optional[str] = None,
        gridded_wind_diurnal: Optional[str] = None,
        gridded_wind_diurnal_airtemp: Optional[str] = None,
        gridded_wind_diurnal_cldcvr: Optional[str] = None,
        gridded_wind_diurnal_long: Optional[str] = None,
        gridded_wind_diurnal_date: Optional[str] = None,
        gridded_wind_diurnal_time: Optional[str] = None,
        wind_spd_units: int = 0,
        wind_speed: Union[int, float] = 0,
        wind_direction: Union[int, float] = 0,
        foliar_mc: Union[int, float] = 100,
        crown_fire_method: str = 'Finney',
        num_processors: int = 1,
        mtt_resolution: Union[int, float] = 100,
        mtt_sim_time: int = 0,
        mtt_travel_path_interval: int = 500,
        mtt_spot_probability: float = 0,
        mtt_spot_delay: int = 0,
        mtt_ign_file_path: Optional[str] = None,
        mtt_barrier_file: Optional[str] = None,
        mtt_fill_barriers: Optional[int] = None,
        mtt_spotting_seed: Optional[int] = None,
        mtt_node_spread_num_lat: int = 6,
        mtt_node_spread_num_vert: int = 4,
        tom_treat_res: Optional[int] = None,
        tom_treat_ign_file: Optional[str] = None,
        tom_treat_ideal_lndscp: Optional[str] = None,
        tom_treat_iter: Optional[int] = None,
        tom_treat_dim: Union[float, int] = None,
        tom_treat_frac: Optional[float] = None,
        tom_treat_opp_only: Optional[int] = None,
        far_start_time: Optional[str] = None,
        far_end_time: Optional[str] = None,
        far_timestep: Optional[int] = None,
        far_dist_res: Optional[Union[int, float]] = None,
        far_per_res: Optional[Union[int, float]] = None,
        far_spot_grd_res: Optional[int] = None,
        far_spot_prob: Optional[float] = None,
        far_spot_ign_delay: Optional[int] = None,
        far_min_ign_vrtx_dist: Optional[int] = None,
        far_min_spot_dist: Optional[int] = None,
        far_spotting_seed: Optional[int] = None,
        far_accel_on: Optional[int] = None,
        far_ign_file: Optional[str] = None,
        far_burn_periods: Optional[Union[list[int, str], tuple[int, str]]] = None,
        far_barrier_file: Optional[str] = None,
        far_fill_barriers: Optional[int] = None,
        far_ros_adjust_file: Optional[str] = None
) -> str:
    """
    Function to generate a FlamMap, MTT, TOM, or Farsite input file.
    :param out_dir: Path to output folder
    :param out_name: Name of the input file
    :param suppress_messages: if True, do not print messages from this function
    :param app_select: The name of the selected fire modelling application.
        Options are "FlamMap", "MTT", "TOM", "Farsite". Default = "FlamMap".
    :param output_list: List of requested output datasets. If left blank, default values will be used based on
        the app_select variable
    :param cond_period_end: The month, day and military time of end of conditioning period.
    :param fuel_moisture_data: List[0] The number of fuel model entries, and List[1] the actual Wind Data records.
        NOTE: Fuel Model 0 is required! This is the default moistures to use when a fuel model is
        encountered in the lcp file that does not have an entry in the inputs file.
    :param custom_fuels_file: The complete path and name of the desired custom fuels file to use.
    :param raws_units: Either the string English or Metric indicating the units for the weather data in the RAWS
        section as well as the RAWS_ELEVATION.
    :param raws_elev: The elevation of the weather observations in the RAWS section. Units are indicated by the
        RAWS_UNITS switch, feet when RAWS_UNITS is English, meters when RAWS_UNITS is metric.
    :param raws_data: The number of sequential hourly weather data entries, followed by X number of hourly
        weather data records, 1 per line. Note that this switch must be used with the RAWS_ELEVATION switch,
        and this switch can not be used with the WEATHER_DATA and WIND_DATA switches.
        Units are indicated by the RAWS_UNITS switch which is also required when using RAWS weather data.
    :param weather_data_units: Either METRIC or ENGLISH. Note: If not used weather data is assumed to be in
        English units.
    :param weather_data: List[0] The number of weather data entries, List[1] X number of weather data records,
        1 per line. NOTE: The weather data records must be in sequential order! No skipping days!
    :param wind_data_units: Either METRIC or ENGLISH. Note: If not used wind data is assumed to be in
        English units.
    :param wind_data: List[0] The number of Wind Data records, and List[1] the actual Wind Data records.
    :param spread_direction_from_north: The azimuth to offset spread directions. Note: Usage of this switch is rare.
        Valid values: 0-360.
    :param spread_direction_from_max: The relative spread direction (azimuth) from the maximum.
        Valid range: 0-360.
    :param gridded_wind_spd_file: The path to an ASCII or TIFF grid of wind velocities.
        Must be an integer raster. Specify the units with the "wind_spd_units" variable.
    :param gridded_wind_dir_file: The path to an ASCII or TIFF grid of wind azimuths in degrees.
        Must be an integer raster.
    :param gridded_wind_gen: Either ‘Yes’ or ‘No’. Default is ‘No’. This switch will be ignored if the gridded
        winds resolution switch is not present or invalid.
    :param gridded_wind_res: The resolution to use for gridded winds in the same units as the landscape file.
    :param gridded_wind_diurnal: Either ‘Yes’ or ‘No’. Default is ‘No’. This switch will be ignored if the
        gridded winds usage is set to ‘No’. Setting this switch to ‘Yes’ requires all other gridded winds
        settings be used for Diurnal calculations to be used.
    :param gridded_wind_diurnal_airtemp: The air temperature in degrees Fahrenheit.
    :param gridded_wind_diurnal_cldcvr: The percent cloud cover. (0.0 – 100.0)
    :param gridded_wind_diurnal_long: The longitude in decimal degrees. (-180.0 – 180.0)
    :param gridded_wind_diurnal_date: mm dd yyyy, where mm is the month (1 – 12), dd is the day of the
        month (1 – 31, must be a valid day for the month), yyyy is the calendar year (e.g. 2009).
    :param gridded_wind_diurnal_time: ss mm hh tz, where ss is seconds (0 – 59); mm is minutes (0 – 59);
        hh is hours (0 - 23); tz is time zone (-12 – 12), indicates time zone offset from GMT for example,
        -7 is Mountain Standard Time.
    :param wind_spd_units: An integer designating units for wind speed input and output according to the following:
        0 - MPH, 1 - KPH, 2 - m/sec, 3 - ft/min. The default is WIND_SPEED_UNITS: 0,
        which will input/output data in MPH. NOTE: This switch applies to constant (global) wind speeds and
        gridded wind speed file wind speeds only. Wind speeds in WXS and WND (deprecated) files use the
        ENGLISH (MPH) or METRIC (KPH) units designated in the file or embedded in the inputs file with the
        RAWS_UNITS or WIND_DATA_UNITS switches.
    :param wind_speed: The wind speed to use. Valid range: 0-200.
    :param wind_direction: The azimuth of the wind direction (that wind is coming from) to use.
        Valid range: 0-360, -1, -2. # Downhill = -2, uphill = -1, azimuth = 0 - 360.
    :param foliar_mc: The foliar moisture content in percent. Valid range: 2-200. The default is 100,
        which will be used if this switch is not present.
    :param crown_fire_method: Either Finney or ScottReinhardt. Note: If not used the Finney crown fire
        method will be used.
    :param num_processors: The number of processors for FlamMap to use. Valid Range: 1..Number of logical
        processors on the machine. If greater than the number of available processors, 1 will be used.
        The default value is 1 if this switch is not present.
    :param mtt_resolution: The resolution to run MTT. Outputs will be generated at the provided grid resolution.
    :param mtt_sim_time: The number of minutes to burn the fire. Set to 0 to burn the entire landscape.
    :param mtt_travel_path_interval: The distance (in landscape units) for travel path creation.
    :param mtt_spot_probability: The probability of a spot creating an ignition.
        Valid Range: 0.0 – 1.0.
    :param mtt_spot_delay: The delay (in minutes) for a spot ignition to start burning.
        Valid Range: 0 – 60.
    :param mtt_ign_file_path: The complete or relative path to the ignition shape file. Optionally, call
        SetIgnition() after loading the inputs file.
    :param mtt_barrier_file: The complete or relative path to the barriers shape file. Optionally, call
        SetBarriers() after loading the inputs file.
    :param mtt_fill_barriers: Either 1 for true or 0 for false.
    :param mtt_spotting_seed: A number (integer from 0-999999) that is used in randomly generating spot
        fire occurrence and locations. This number generates automatically for newly created analyses.
        There is generally no need for users to change this value. When an analysis is copied, the
        Spotting Seed is copied along with other settings. Two analyses with the same settings (including
        Spotting Seed) should generate the same spotting results.
        ** NOTE if MTT_SPOT_PROBABILITY is 0, this switch is not needed and will be ignored.
        ** NOTE if MTT_SPOT_PROBABILITY is >0, this switch is an optional input.
    :param mtt_node_spread_num_lat: The number of columns MTT searches spread times. Switch is optional, default is 6.
    :param mtt_node_spread_num_vert: The number of rows MTT searches spread times. Switch is optional, default is 4.
    :param tom_treat_res: Optional switch for TOM. If running TOM all switches are required.
        The resolution to run TOM. Outputs will be generated at grid resolution X
    :param tom_treat_ign_file: Optional switch for TOM. If running TOM all switches are required.
        The complete or relative path to the ignition shape file.
    :param tom_treat_ideal_lndscp: Optional switch for TOM. If running TOM all switches are required.
        The complete or relative path to the ideal landscape file.
    :param tom_treat_iter: Optional switch for TOM. If running TOM all switches are required.
        An integer representing the number of iterations per treatment level. Valid Range: 1 - 5.
        Generally little benefit if greater than 1.
    :param tom_treat_dim: Optional switch for TOM. If running TOM all switches are required.
        The distance in meters that TOM uses for treatment size and maximum distance a fire can travel
        before expecting a treatment unit.
    :param tom_treat_frac: Optional switch for TOM. If running TOM all switches are required. A floating
        point value representing the proportion of the landscape that can be treated. Valid Range: 0.10 – 0.30
    :param tom_treat_opp_only: Optional switch for TOM. If running TOM all switches are required.
        A Boolean flag indicating whether only treat opportunities layer should be generated.
        Acceptable values are either 0 or 1.
    :param far_start_time: MM DD HHmm, where MM is Month (1-12), DD is day of month, HH is hour(0-24) and
        mm is minute (0-59) of the fire start time.
    :param far_end_time: MM DD HHmm, where MM is Month (1-12), DD is day of month, HH is hour(0-24) and
        mm is minute(0-59) of the fire end time (end of simulation).
    :param far_timestep: The Actual Time Step in minutes. Note there is no Secondary Time Step in the
        Farsite DLL.
    :param far_dist_res: A real number representing the distance resolution. Farsite DLL will check for new
        fire characteristics when this distance has been covered within a time step.
    :param far_per_res: A real number representing the Farsite Perimeter Resolution. Farsite will have fire
        vertices every X meters along a perimeter while burning at each time step.
    :param far_spot_grd_res: The resolution of the background spotting grid. NOTE: Resolution should be an
        integer divisor of the landscape resolution, i.e. if landscape resolution is 30m,
        X should be 30, 15, 10, 6, 5, 3, 2, or 1. The intent is for the background spotting grid to subdivide
        landscape cells. The background spotting grid is used to prevent more than one spot fire being started
        in a spotting grid cell, so adjust this parameter to your tolerance for spot fire density.
    :param far_spot_prob: A real number from 0.0 – 1.0 representing the probability that an ember can survive
        to intersect the landscape. This probability check is done after an ember is lofted but before ember
        flight. Note: Farsite generates a lot of embers. Generally, this probability should not be higher than
        0.1 or Farsite will spend a great deal of time resolving perimeters of spots created by embers.
    :param far_spot_ign_delay: An integer representing the delay time in minutes before a spot fire is started
        after an ember lands on a burnable substrate. Note: This switch should probably be set to zero (0) when
        acceleration is on.
    :param far_min_ign_vrtx_dist: The minimum distance, in meters, between fire ignition vertices placed along
        the given ignition shapefile. Valid range: 7-10000.
    :param far_min_spot_dist: The distance in meters an ember must travel before it can start a spot fire.
        This switch was added to speed up Farsite resolving fire polygons that where generally overrun by
        surface fire spread.
    :param far_spotting_seed: A number (integer from 0-999999) that is used in randomly generating spot fire
        occurrence and locations. This number generates automatically for newly created analyses.
        There is generally no need for users to change this value. When an analysis is copied, the
        Spotting Seed is copied along with other settings. Two analyses with the same settings
        (including Spotting Seed) should generate the same spotting results.
        ** NOTE if FARSITE_SPOT_PROBABILITY is 0, this switch is not needed and will be ignored.
        ** NOTE if FARSITE_SPOT_PROBABILITY is >0, this switch is an optional input.
    :param far_accel_on: Either 0 for no acceleration or 1 to use acceleration.
    :param far_ign_file: The complete path to the ignition shape file.
    :param far_burn_periods: List[0] The number of burn period entries, List[1] X burn period entries on the
        next X lines in the inputs file.
    :param far_barrier_file: The path to the barrier shape file. No barriers are required.
        Note: Farsite DLL does not create a perimeter with barriers as does FARSITE4, but sets
        the underlying fuels to non-burnable for every pixel in the landscape that the barrier crosses.
    :param far_fill_barriers: Either 0 for false (no barrier fill) or 1 for true (fill the barriers).
        Farsite DLL will set all of the pixels inside a barrier polygon to non-burnable.
    :param far_ros_adjust_file: The name of the rate of spread adjustment file to use.
    :return: the path to the resulting input file

    **output_list**
        The following outputs are available for each App as described...

        * Note: At least one VALID output switch is mandatory. One switch per line is allowed in the inputs file.

        All Apps:
            FLAMELENGTH (raster grid)
                Output is a gridded file of flame length (units = meters).
                This output switch is always available.
            SPREADRATE (raster grid)
                Output is a gridded file of rate of spread (units = m/min).
                This output switch is always available.
            INTENSITY (raster grid)
                Output is a gridded file of fireline intensity (units = kW/m).
                This output switch is always available.
            HEATAREA (raster grid)
                Output is a gridded file of heat per unit area (units = kJ/m2).
                This output switch is always available.
            CROWNSTATE (raster grid)
                Output is a gridded file of crown fire activity (units = class).
                This output switch is always available.
        FlamMap, MTT, and TOM Only:
            MIDFLAME (raster grid)
                Output is a gridded file of mid-flame wind speed (units = mph).
                This output switch is always available.
            HORIZRATE (raster grid)
                Output is a gridded file of horizontal rate of spread (units = m/min).
                This output switch is always available.
            MAXSPREADDIR (raster grid)
                Output is a gridded file of maximum spread direction (units = degrees).
                This output switch is always available.
            ELLIPSEDIM_A (raster grid)
                Output is a gridded file of rate of spread for ellipse dimension A (units = m/min).
                This output switch is always available.
            ELLIPSEDIM_B (raster grid)
                Output is a gridded file of rate of spread for ellipse dimension B (units = m/min).
                This output switch is always available.
            ELLIPSEDIM_C (raster grid)
                Output is a gridded file of rate of spread for ellipse dimension C (units = m/min).
                This output switch is always available.
            MAXSPOT (raster grid)
                Output is a gridded file of maximum spotting distance (units = meters).
                This output switch is always available.
            MAXSPOT_DIR (raster grid)
                Output is a gridded file of maximum spotting direction (units = degrees).
                This output switch is always available.
            MAXSPOT_DX (raster grid)
                Output is a gridded file of maximum spotting distance (units = meters).
                This output switch is always available.
            CROWNFRACTIONBURNED (raster grid)
                Output is a gridded file of crown fraction burned (units = percent).
                This output switch is always available.
            SOLARRADIATION (raster grid)
                Output is a gridded file of solar radiation (units = W/m2).
                This output switch is only available when using fuel conditioning.
            FUELMOISTURE1 (raster grid)
                Output is a gridded file of 1 hr fuel moisture (units = percent).
                This output switch is only available when using fuel conditioning.
            FUELMOISTURE10 (raster grid)
                Output is a gridded file of 10 hr fuel moisture (units = percent).
                This output switch is only available when using fuel conditioning.
            FUELMOISTURE100 (raster grid)
                Output is a gridded file of 100 hr fuel moisture (units = percent).
                This output switch is only available when using fuel conditioning.
            FUELMOISTURE1000 (raster grid)
                Output is a gridded file of 1000 hr fuel moisture (units = percent).
                This output switch is only available when using fuel conditioning.
            WINDDIRGRID (raster grid)
                Output is a gridded file of wind direction (units = degrees).
                This output switch is only available when using GRIDDED WINDS.
            WINDSPEEDGRID (raster grid)
                Output is a gridded file of wind speed (units = mph).
                This output switch is only available when using GRIDDED WINDS.
            WINDVECTOR (KMZ)
                Output is a KMZ of wind vectors.
                Requires GRIDDED_WINDS_GENERATE to be "yes".
        MTT Only:
            MTT_ROS or MTTSPREADRATE (raster grid)
                Output is a gridded file of MTT rate of spread (units = m/min).
                This output switch is always available.
            MTT_ARRIVAL or MTTARRIVALTIME (raster grid)
                Output is a gridded file of MTT arrival time (units = minutes).
                This output switch is always available.
            MTT_CONTOUR or MTTCONTOUR (raster grid)
                Output is a gridded file of MTT arrival time contpurs (units = minutes).
                This output switch is always available.
            MTT_INTENSITY or MTTINTENSITY (raster grid)
                Output is a gridded file of MTT fireline intensity (units = kW/m).
                This output switch is always available.
            MTT_MAJORPATHS or MTTMAJORPATHS (shapefile)
                Output is a shapefile of MTT major flow paths.
                This output switch is always available.
            MTT_FLOWPATHS or MTTFLOWPATHS (shapefile)
                Output is a shapefile of MTT flow paths.
                This output switch is always available.
            MTT_EMBERS or MTTEMBERS (shapefile)
                Output is a shapefile of MTT ember locations associated with spotting.
                Switch requires MTT_SPOT_PROBABILITY to be >0.
        Farsite Only:
            ARRIVALTIME (raster grid)
                Output is a gridded file for FARSITE Arrival Time (units = minutes).
                This output switch is always available.
            SPREADDIR (raster grid)
                Output is a gridded file for FARSITE Spread Direction (units = degrees).
                This output switch is always available.
            RXINTENSITY (raster grid)
                Output is a gridded file for FARSITE Reaction Intensity (units = kJ/m2-min).
                This output switch is always available.
            IGNITION (raster grid)
                Output is a gridded file for FARSITE Ignition (units = class).
                This output switch is always available.
            FARSITEPERIMETERS (shapefile)
                Output is a shapefile containing a perimeter for each timestep.
                This output switch is always available.
            FARSITESPOTFIRES (shapefile)
                Output is a shapefile with the locations where spot fires occurred.
                This output switch is always available.
            FARSITETIMINGS (text file)
                Output is a text file containing the input information for the model run,
                information regarding the system on which the model was run, the number of
                vertices (not cells) on the edge of the landscape that burned, as well as the
                amount of time that it took the FARSITE model to complete
        Default Outputs (if output_list is None):
            FLAMELENGTH, SPREADRATE, INTENSITY, HEATAREA, CROWNSTATE

    **cond_period_end**
        Example:
            * CONDITIONING_PERIOD_END: 08 01 1600
    **fuel_moisture_data**
        Fuel moisture entry format:
            * Model FM1 FM10 FM100 FMLiveHerb FMLiveWoody
        Example:
            * FUEL_MOISTURES_DATA: 3
            * # Model F1 F10 F100 FLH FLW
            * 0 2 2 3 4 5
            * 1 4 3 6 10 16
            * 2 4 3 19 10 16
    **custom_fuels_file**
        Example:
            * CUSTOM_FUELS_FILE: 'C:/data/customfuels.fmd'
    **raws_units**
        Example:
            * RAWS_UNITS: English
    **raws_elev**
        Example:
            * RAWS_ELEVATION: 3532
    **raws_data**
        Entry format:
            * Year Mth Day HHMM Temp RH Pcp WS WDir CC
        Variable descriptions:
            * Year = Year
            * Mth = month,
            * Day = day of month,
            * HHMM = time of record (2 digits for hour, two digits for minute)
            * Temp = temperature at time of record
            * RH = relative humidity at time of record
            * Pcp = hourly precipitation for the hour ending at time of record
            * WS = wind speed at time of record
            * WDir = azimuth of wind direction at time of record
            * CC = cloud cover as integer percent (0 - 100) at time of record
        Example:
            * RAWS: 5
            * 2018 3 23 0700 78 18 0.00 2 177 40
            * 2018 3 23 0800 76 22 0.00 3 235 35
            * 2018 3 23 0900 74 22 0.00 3 236 0
            * 2018 3 23 1000 72 22 0.00 7 233 0
            * 2018 3 23 1100 71 22 0.00 1 230 30
    **weather_data_units**
        Example:
            * WEATHER_DATA_UNITS: METRIC
    **weather_data**
        Entry format:
            * Mth Day Pcp mTH xTH mT xT xH mH Elv PST PET
        Variable descriptions:
            * Mth = month,
            * Day = day,
            * Per = precip in hundredths of an inch (integer e.g. 10 = 0.1 inches),
            * mTH = min_temp_hour 0-2400,
            * xTH = max_temp_hour 0 - 2400,
            * mT = min_temp,
            * xT = max_temp,
            * mH = max_humidity,
            * xH = min_humidity,
            * Elv = elevation,
            * PST = precip_start_time 0-2400
            * PET = precip_end_time 0-2400
        Example:
            * # NOTE: do not leave any blank values
            * WEATHER_DATA: 17
            * 7 17 0 400 1500 53 94 36 8 4478 0 0
            * 7 18 0 500 1400 52 94 43 9 4478 0 0
            * 7 19 0 500 1300 55 96 48 8 4478 0 0
            * 7 20 0 500 1200 57 90 48 12 4478 0 0
            * 7 21 0 600 1200 59 89 59 16 4478 0 0
            * 7 22 0 500 1500 52 88 59 11 4478 0 0
            * 7 23 0 400 1300 55 92 54 10 4478 0 0
            * 7 24 0 400 1400 54 96 50 9 4478 0 0
            * 7 25 0 500 1300 52 95 48 7 4478 0 0
            * 7 26 50 600 1400 54 93 38 11 4478 1100 1700
            * 7 27 0 400 1300 55 93 41 7 4478 0 0
            * 7 28 0 500 1500 53 93 38 9 4478 0 0
            * 7 29 0 500 1300 56 91 35 11 4478 0 0
            * 7 30 0 500 1500 53 94 46 11 4478 0 0
            * 7 31 0 500 1300 55 93 45 9 4478 0 0
            * 8 1 0 500 1400 53 96 46 10 4478 0 0
            * 8 2 0 400 1200 55 91 44 2 4478 0 0
    **wind_data_units**
        Example:
            * WIND_DATA_UNITS: METRIC
    **wind_data**
        Example:
            * WIND_DATA: 7
            * # Mth Day Hour Speed Direction CloudCover
            * 7 17 0 3 114 0
            * 7 17 100 1 31 0
            * 7 17 200 1 127 0
            * 7 17 300 5 114 0
            * 7 17 400 2 58 0
            * 7 17 500 2 22 0
            * 7 17 600 1 53 0
            Wind Data records should be in ascending order, and should cover the same time frame as the
            weather data records. Small gaps are allowed.
        For Farsite:
            Farsite will burn using the most available wind record so hourly wind records are desired.
    **gridded_wind_spd_file**
        Example:
            * GRIDDED_WIND_SPEED_FILE: C:/Data/velocity_20_225.asc
    **gridded_wind_dir_file**
        Example:
            * GRIDDED_WINDS_DIRECTION_FILE: C:/Data/angle_20_225.asc
    **gridded_wind_gen**
        Example:
            * Example: GRIDDED_WINDS_GENERATE: Yes
    **gridded_wind_res**
        Example:
            * GRIDDED_WINDS_RESOLUTION: 200
    **gridded_wind_diurnal**
        Example:
            * GRIDDED_WINDS_DIURNAL: Yes
    **gridded_wind_diurnal_airtemp**
        Example:
            * GRIDDED_WINDS_DIURNAL_AIRTEMP: 84.5
    **gridded_wind_diurnal_cldcvr**
        Example:
            * GRIDDED_WINDS_DIURNAL_CLOUDCOVER: 15.0
    **gridded_wind_diurnal_long**
        Example:
            * GRIDDED_WINDS_DIURNAL_LONGITUDE: -114.0
    **gridded_wind_diurnal_date**
        Example:
            * GRIDDED_WINDS_DIURNAL_DATE: 03 16 2009
    **gridded_wind_diurnal_time**
        Example:
            * GRIDDED_WINDS_DIURNAL_TIME: 0 00 14 -7
    **wind_speed**
        Example:
            * WIND_SPEED: 15
    **wind_direction**
       Example:
           * WIND_DIRECTION: 280
    **foliar_mc**
        Example:
            * FOLIAR_MOISTURE_CONTENT: 90
    **crown_fire_method**
        Example:
            * CROWN_FIRE_METHOD: ScottReinhardt
    **mtt_sim_time**
        Example:
            * MTT_SIM_TIME: 700
    **mtt_travel_path_interval**
        Example:
            * MTT_TRAVEL_PATH_INTERVAL: 500
    **mtt_spot_probability**
        Example:
            * MTT_SPOT_PROBABILITY: 0.1
    **mtt_spot_delay**
        Example:
            * MTT_SPOT_DELAY: 10
    **mtt_ign_file_path**
        Example:
            * MTT_ IGNITION _FILE: C:/ignitions.shp
    **mtt_barrier_file**
        Example:
            * MTT_BARRIER_FILE: C:/barriers.shp
    **mtt_fill_barriers**
        Example:
            * MTT_FILL_BARRIERS: 1
    **mtt_node_spread_num_lat**
        Example:
            * NodeSpreadNumLat: 6
    **mtt_node_spread_num_vert**
        Example:
            * NodeSpreadNumVert: 4
    **tom_treat_ign_file**
        Example:
            * TREAT_ IGNITION _FILE: C:/TOMignitions.shp
    **tom_treat_ideal_lndscp**
        Example:
            * TREAT_ IDEAL_LANDSCAPE: C:/IdealLandscape.lcp
    **far_start_time**
        Example:
            * FARSITE_START_TIME: 08 07 1000
    **far_end_time**
        Example:
            * FARSITE_END_TIME: 08 10 1800
    **far_timestep**
        Example:
            * FARSITE_TIME_STEP: 60
    **far_dist_res**
        Example:
            * FARSITE_DISTANCE_RES: 30.0
    **far_per_res**
        Example:
            * FARSITE_PERIMETER_RES: 60.0
    **far_spot_grd_res**
        Example:
            * FARSITE_SPOT_GRID_RESOLUTION: 15
    **far_spot_prob**
        Example:
            * FARSITE_SPOT_PROBABILITY: 0.01
    **far_spot_ign_delay**
        Example:
            * FARSITE_SPOT_IGNITION_DELAY: 15
    **far_min_spot_dist**
        Example:
            * FARSITE_MINIMUM_SPOT_DISTANCE: 30
    **far_accel_on**
        Example:
            * FARSITE_ACCELERATION_ON: 1
    **far_ign_file**
        Example:
            * FARSITE_IGNITION_FILE: C:/Data/ignit.shp
    **far_burn_periods**
        Entry format:
            * MM DD HHmm HHmm
        Variable descriptions:
            * MM is the month (01-12),
            * DD is the day of the month,
            * the first HHmm is the burn period start hour and minute,
            * the second HHmm is the burn period end hour and minute.
            Note that if no burn periods are used Farsite DLL will burn for the entire simulation period. Also,
            there can be more than one burn period per day but they must not overlap.
        Example:
            * FARSITE_BURN_PERIODS: 4
            * 08 07 1000 1800
            * 08 08 1000 1800
            * 08 09 1000 1800
            * 08 10 1000 1800
    **far_barrier_file**
        Example:
            * FARSITE_BARRIER_FILE: C:/Data/barrier.shp
    **far_fill_barriers**
        Example:
            * FARSITE_FILL_BARRIERS: 1
    """
    if not suppress_messages:
        print(f'\n<<<<< [flammap_cli.py] Generating {app_select} Input File >>>>>')

    # Delete existing output file
    out_path = os.path.join(out_dir, f'{out_name}.input')
    if os.path.exists(out_path):
        os.remove(out_path)

    # Change the following values for each model run
    try:
        with open(out_path, 'w') as file:
            # Implement Header Text
            file.write(f'#FLAMMAP INPUT FILE FOR {out_name}\n')
            if app_select == 'FlamMap':
                file.write('FlamMap-Inputs-File-Version-1\n')
            elif app_select in ['MTT', 'TOM']:
                file.write('ShortTerm-Inputs-File-Version-1\n')
            else:
                file.write('FARSITE INPUTS FILE VERSION 1.0\n')
            # Implement Base/Common Fuel Moisture Switches
            if app_select in ['FlamMap', 'MTT', 'TOM']:
                if cond_period_end:
                    file.write(f'CONDITIONING_PERIOD_END: {cond_period_end}\n')
            if fuel_moisture_data:
                file.write(f'FUEL_MOISTURES_DATA: {fuel_moisture_data[0]}\n')
                file.write(f'{fuel_moisture_data[1]}\n')
                file.write('\n')
            if custom_fuels_file:
                file.write(f'CUSTOM_FUELS_FILE: {custom_fuels_file}\n')
        with open(out_path, 'a') as file:
            # Implement Base/Common Switches
            if raws_units:
                file.write(f'RAWS_UNITS: {raws_units}\n')
                file.write('\n')
            if raws_elev:
                file.write(f'RAWS_ELEVATION: {raws_elev}\n')
            if raws_data:
                file.write(f'RAWS: {raws_data[0]}\n')
                file.write(f'{raws_data[1]}\n')
                file.write('\n')
            if weather_data_units:
                file.write(f'WEATHER_DATA_UNITS: {weather_data_units}\n')
            if weather_data:
                file.write(f'WEATHER_DATA: {weather_data[0]}\n')
                file.write(f'{weather_data[1]}\n')
                file.write('\n')
            if wind_data_units:
                file.write(f'WIND_DATA_UNITS: {wind_data_units}\n')
            if wind_data:
                file.write(f'WIND_DATA: {wind_data[0]}\n')
                file.write(f'{wind_data[1]}\n')
                file.write('\n')
            if spread_direction_from_north:
                file.write(f'SPREAD_DIRECTION_FROM_NORTH: {spread_direction_from_north}\n')
            if spread_direction_from_max:
                file.write(f'SPREAD_DIRECTION_FROM_MAX: {spread_direction_from_max}\n')
            if gridded_wind_spd_file:
                file.write(f'GRIDDED_WIND_SPEED_FILE: {gridded_wind_spd_file}\n')
            if gridded_wind_dir_file:
                file.write(f'GRIDDED_WINDS_DIRECTION_FILE: {gridded_wind_dir_file}\n')
            if gridded_wind_gen:
                file.write(f'GRIDDED_WINDS_GENERATE: {gridded_wind_gen}\n')
            if gridded_wind_res:
                file.write(f'GRIDDED_WINDS_RESOLUTION: {gridded_wind_res}\n')
            if gridded_wind_diurnal:
                file.write(f'GRIDDED_WINDS_DIURNAL: {gridded_wind_diurnal}\n')
            if gridded_wind_diurnal_airtemp:
                file.write(f'GRIDDED_WINDS_DIURNAL_AIRTEMP: {gridded_wind_diurnal_airtemp}\n')
            if gridded_wind_diurnal_cldcvr:
                file.write(f'GRIDDED_WINDS_DIURNAL_CLOUDCOVER: {gridded_wind_diurnal_cldcvr}\n')
            if gridded_wind_diurnal_long:
                file.write(f'GRIDDED_WINDS_DIURNAL_LONGITUDE: {gridded_wind_diurnal_long}\n')
            if gridded_wind_diurnal_date:
                file.write(f'GRIDDED_WINDS_DIURNAL_DATE: {gridded_wind_diurnal_date}\n')
            if gridded_wind_diurnal_time:
                file.write(f'GRIDDED_WINDS_DIURNAL_TIME: {gridded_wind_diurnal_time}\n')

            file.write(f'WIND_SPEED_UNITS: {wind_spd_units}\n')
            file.write(f'WIND_SPEED: {wind_speed}\n')
            file.write(f'WIND_DIRECTION: {wind_direction}\n')
            file.write(f'FOLIAR_MOISTURE_CONTENT: {foliar_mc}\n')
            file.write(f'CROWN_FIRE_METHOD: {crown_fire_method}\n')
            file.write(f'NUMBER_PROCESSORS: {num_processors}\n')
            file.write('\n')

            # Implement Minimum Travel Time (MTT) Switches
            if app_select == 'MTT':
                file.write(f'MTT_RESOLUTION: {mtt_resolution}\n')
                file.write(f'MTT_SIM_TIME: {mtt_sim_time}\n')
                file.write(f'MTT_TRAVEL_PATH_INTERVAL: {mtt_travel_path_interval}\n')
                file.write(f'MTT_SPOT_PROBABILITY: {mtt_spot_probability}\n')
                file.write(f'MTT_SPOT_DELAY: {mtt_spot_delay}\n')
                file.write(f'MTT_IGNITION_FILE: {mtt_ign_file_path}\n')
                if mtt_barrier_file:
                    file.write(f'MTT_BARRIER_FILE: {mtt_barrier_file}\n')
                if mtt_fill_barriers:
                    file.write(f'MTT_FILL_BARRIERS: {mtt_fill_barriers}\n')
                if mtt_spotting_seed:
                    file.write(f'SPOTTING_SEED: {mtt_spotting_seed}\n')
                if mtt_node_spread_num_lat:
                    file.write(f'NodeSpreadNumLat: {mtt_node_spread_num_lat}\n')
                if mtt_node_spread_num_vert:
                    file.write(f'NodeSpreadNumVert: {mtt_node_spread_num_vert}\n')
                file.write('\n')

            # Implement Treatment Optimization Model (TOM) Switches
            if app_select == 'TOM':
                if tom_treat_res:
                    file.write(f'TREAT_RESOLUTION: {tom_treat_res}\n')
                if tom_treat_ign_file:
                    file.write(f'TREAT_IGNITION_FILE: {tom_treat_ign_file}\n')
                if tom_treat_ideal_lndscp:
                    file.write(f'TREAT_IDEAL_LANDSCAPE: {tom_treat_ideal_lndscp}\n')
                if tom_treat_iter:
                    file.write(f'TREAT_ITERATIONS: {tom_treat_iter}\n')
                if tom_treat_dim:
                    file.write(f'TREAT_DIMENSION: {tom_treat_dim}\n')
                if tom_treat_frac:
                    file.write(f'TREAT_FRACTION: {tom_treat_frac}\n')
                if tom_treat_opp_only:
                    file.write(f'TREAT_OPPORTUNITIES_ONLY: {tom_treat_opp_only}\n')
                file.write('\n')

            # Implement Farsite Switches
            if app_select == 'Farsite':
                if far_start_time:
                    file.write(f'FARSITE_START_TIME: {far_start_time}\n')
                if far_end_time:
                    file.write(f'FARSITE_END_TIME: {far_end_time}\n')
                if far_timestep:
                    file.write(f'FARSITE_TIMESTEP: {far_timestep}\n')
                if far_dist_res:
                    file.write(f'FARSITE_DISTANCE_RES: {far_dist_res}\n')
                if far_per_res:
                    file.write(f'FARSITE_PERIMETER_RES: {far_per_res}\n')
                if far_spot_grd_res:
                    file.write(f'FARSITE_SPOT_GRID_RESOLUTION: {far_spot_grd_res}\n')
                if far_spot_prob:
                    file.write(f'FARSITE_SPOT_PROBABILITY: {far_spot_prob}\n')
                if far_spot_ign_delay:
                    file.write(f'FARSITE_SPOT_IGNITION_DELAY: {far_spot_ign_delay}\n')
                if far_min_ign_vrtx_dist:
                    file.write(f'FARSITE_MIN_IGNITION_VERTEX_DISTANCE: {far_min_ign_vrtx_dist}\n')
                if far_min_spot_dist:
                    file.write(f'FARSITE_MINIMUM_SPOT_DISTANCE: {far_min_spot_dist}\n')
                if far_spotting_seed:
                    file.write(f'SPOTTING_SEED: {far_spotting_seed}\n')
                if far_accel_on:
                    file.write(f'FARSITE_ACCELERATION_ON: {far_accel_on}\n')
                if far_ign_file:
                    file.write(f'FARSITE_IGNITION_FILE: {far_ign_file}\n')
                if far_burn_periods:
                    file.write(f'FARSITE_BURN_PERIODS: {far_burn_periods[0]}\n')
                    file.write(f'{far_burn_periods[1]}\n')
                if far_barrier_file:
                    file.write(f'FARSITE_BARRIER_FILE: {far_barrier_file}\n')
                if far_fill_barriers:
                    file.write(f'FARSITE_FILL_BARRIERS: {far_fill_barriers}\n')
                if far_ros_adjust_file:
                    file.write(f'ROS_ADJUST_FILE: {far_ros_adjust_file}\n')
                file.write('\n')

            # Implement Output Switches
            file.write('#REQUESTED OUTPUTS\n')
            if output_list:
                # Write user provided outputs
                for output in output_list:
                    file.write(f'{output}:\n')
            else:
                # Write default outputs
                file.write('FLAMELENGTH:\n'
                           'SPREADRATE:\n'
                           'INTENSITY:\n'
                           'HEATAREA:\n'
                           'CROWNSTATE\n')

        if not suppress_messages:
            print('Input file complete')
    except FileNotFoundError:
        print('The input file directory does not exist')
    except Exception as err:
        print(err)

    return out_path


def runApp(app_select: str,
           command_file_path: str,
           app_exe_path: Optional[str] = None,
           suppress_messages: bool = False) -> tuple[str, str]:
    """
    Function to run the selected fire app through the command line interface
    :param app_select: The name of the selected fire modelling application.
        Options are "FlamMap", "MTT", "TOM", "Farsite"
    :param command_file_path: path to command file
    :param app_exe_path: path to the app executable file
    :param suppress_messages: suppress intermediate print statements during program execution
    :return: A tuple containing the standard output messages, and the CLI app errors
    """
    # Check if the FB folder exists within the supplementary_data folder
    # If not, download the application data
    if not os.path.exists(fb_path):
        downloadApps()

    if app_exe_path is None:
        # Get the name of the application executable file
        app_exe_path = app_exe_dict.get(app_select, None)

    if app_exe_path is not None:
        if not suppress_messages:
            print(f'\n<<<<< [flammap_cli.py] Running {app_select} >>>>>')

        # Run fire model through command line interface
        if not suppress_messages:
            print('Running CLI command...')
        app_cli = subprocess.Popen(
            [app_exe_path, command_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(command_file_path)
        )
        stdout, stderr = app_cli.communicate()
        if not suppress_messages:
            print(f'{stdout}\n{stderr}')

        del app_cli

        # Delete the current CLI app process if it's still running
        try:
            worker_proc = psutil.Process(os.getpid())
            for child in worker_proc.children(recursive=True):  # Kill all child processes running app
                if app_name_dict[app_select] in child.name():
                    child.kill()
        except psutil.NoSuchProcess:
            pass

        if not suppress_messages:
            print(f'<<<<< {app_select} modelling complete >>>>>')
    else:
        # Raise a value error
        raise ValueError(f'Invalid fire model selected.\n'
                         f'The "app_selection" variable be one of the following:\n'
                         f'{", ".join(app_name_dict.keys())}')

    return stdout, stderr


def appTest(app_selection: str) -> None:
    """
    Function to run the Missoula Fire Lab Command Line Application test datasets
    :param app_selection: The name of the selected fire modelling application.
        Options are "FlamMap", "MTT", "TOM", "Farsite". Default = "FlamMap".
    :return: None
    """
    app_testData_dict = {
        'FlamMap': os.path.join(fb_path, 'TestFlamMap\\SampleData'),
        'MTT': os.path.join(fb_path, 'TestMTT\\SampleData'),
        'TOM': os.path.join(fb_path, 'TestMTT\\SampleData'),
        'Farsite': os.path.join(fb_path, 'TestFARSITE\\SampleData'),
        # 'FSPro': os.path.join(fb_path, 'TestFSPro\\SampleData'),
        # 'SpatialFOFEM': os.path.join(fb_path, 'TestSpatialFOFEM\\SampleData')
    }

    # Get the test application path
    test_data_path = app_testData_dict.get(app_selection, None)

    if test_data_path is not None:
        # Get the command file path
        command_file_path = glob.glob(os.path.join(test_data_path, '*Cmd.txt'))[0]

        # Run the application
        runApp(app_selection, command_file_path)
    else:
        raise ValueError(f'Invalid application selection: Must be one of: {", ".join(app_name_dict.keys())}')

    return


if __name__ == '__main__':
    # Choose app to test the Missoula Fire Lab Command Line Applications
    _app_selection = 'Farsite'  # Options: 'FlamMap', 'MTT', 'Farsite'

    # Test the application
    appTest(app_selection=_app_selection)
