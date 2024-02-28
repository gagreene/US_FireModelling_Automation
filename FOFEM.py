import numpy as np
import pandas as pd
import datetime
import os


def getMidflameWS(selfself, ws, cc, ht, cbh, units):
    """
    :return mid-flame windspeed (m/s)\n
    :param ws = windspeed (km/h or mi/h)\n
    :param cc = canopy cover (fraction)\n
    :param ht = stand ht (m or ft)\n
    :param cbh = canopy base height (m or ft)\n
    :param units = units of input data ("SI" or "IMP")
        SI = metric (10-m ws in km/h, ht in m, cbh in m)\n
        IMP = imperial (20-ft ws in mi/h, ht in ft, cbh in ft)\n
    Divide by 3.6 to convert from km/h to m/s\n
    Divide windspeed by 1.15 to convert from 10-m to 20-ft equivalent (Lawson and Armitage 2008)\n
    Calculate mid-flame windspeed (m/s) using under canopy equations (Albini and Baughman 1979)
          Uc/Uh = 0.555 / (sqrt(f*H) * ln((20 + 0.36*H) / (0.13*H)))\n
          where f = crown ratio * canopy cover (proportion) / 3, H = stand height (ft)\n
    Equations explained well in Andrews (2012) - Modeling wind adjustement factor and
    midflame wind speed for Rothermel's surface fire spread model\n
    """
    if units == 'SI':
        ws /= (3.6 * 1.15)  # convert 10m (km/hr) windspeed to 20ft (m/s) equivalent
        ht *= 3.28084
        cbh *= 3.28084
    elif units == 'IMP':
        ws /= 2.23694
    cr = (ht - cbh) / ht
    f = cr * cc / 3
    if f <= 5 or ht == 0:
        # Return unsheltered midflame windspeed
        # return ws * 0.5
        return ws * 1.83 / np.log((20 + (0.36 * ht)) / (0.13 * ht))
    else:
        # Return sheltered midflame windspeed
        return ws * 0.555 / (np.sqrt(f * ht) * np.log((20 + (0.36 * ht)) / (0.13 * ht)))


def genBurnupInFile(self, outBRN=None,
                    MAX_TIMES=3000, INTENSITY=50.0, IG_TIME=60.0, WINDSPEED=0.0, DEPTH=0.3, AMBIENT_TEMP=27.0,
                    R0=1.83, DR=0.4, TIMESTEP=15.0,
                    SURat_Lit=8200, SURat_DW1=1480, SURat_DW10=394, SURat_DW100=105,
                    SURat_DWk_3_6=39.4, SURat_DWk_6_9=21.9, SURat_DWk_9_20=12.7, SURat_DWk_20=5.91):
    """
    Function generates a Burnup-in.brn file from the input parameters, and saves it at the outBRN location\n
    :return Burnup-in.brn file\n\n

    Required parameters: outBRN\n
    Optional parameters: All other inputs are not required if using default values. Replace otherwise.\n
    :param outBRN = folder/directory to save Burnup-in.brn file\n
    :param MAX_TIMES = Maximum number of iterations burnup does (default = 3000); valid range: 1 - 100000\n
    :param INTENSITY = Intensity of the igniting surface fire (kW/m^2)
                       (default = 50); valid range: 40 - 100000 kW/m^2\n
    :param IG_TIME = Residence time of the ignition surface fire (s)
                     (default = 60, FOFEM's burnup input default = 30); valid range: 10 - 200 s\n
    :param WINDSPEED = Windspeed at the top of the fuelbed (m/s) (default = 0); valid range: 0 - 5 m/s\n
    :param DEPTH = Fuel depth (m) (default = 0.3); valid range: 0.1 - 5 m\n
    :param AMBIENT_TEMP = Ambient air temperature (C) (default = 27); valid range: -40 - 40 C\n
    :param R0 = Fire environment minimum dimension parameter (unitless) (default = 1.83); valid range: any\n
    :param DR = Fire environment increment temp parameter (C) (default = 0.4); valid range: any\n
    :param TIMESTEP = Time step for integration of burning rates (s) (default = 15); valid range: any\n
    :param SURat_Lit = Surface area to volume ratio of litter\n
    :param SURat_DW1 = Surface area to volume ratio of 1 hr down woody fuels\n
    :param SURat_DW10 = Surface area to volume ratio of 10 hr down woody fuels\n
    :param SURat_DW100 = Surface area to volume ratio of 100 hr down woody fuels\n
    :param SURat_DWk_3_6 = Surface area to volume ratio of down woody fuels 3 - 6 in. diameter\n
    :param SURat_DWk_6_9 = Surface area to volume ratio of down woody fuels 6 - 9 in. diameter\n
    :param SURat_DWk_9_20 = Surface area to volume ratio of down woody fuels 9 - 20 in. diameter\n
    :param SURat_DWk_20 = Surface area to volume ratio of down woody fuels >= 20 in. diameter\n
    """
    if outBRN is None:
        raise Exception('No output file/directory specified for Burnup-in.brn file')

    if MAX_TIMES > 100000:
        MAX_TIMES = 100000
    elif MAX_TIMES < 0:
        MAX_TIMES = 0

    if INTENSITY > 100000:
        INTENSITY = 100000
    elif INTENSITY < 0:
        INTENSITY = 0

    if IG_TIME > 200:
        IG_TIME = 200
    elif IG_TIME < 10:
        IG_TIME = 10

    if WINDSPEED > 5:
        WINDSPEED = 5
    elif WINDSPEED < 0:
        WINDSPEED = 0

    if DEPTH > 5:
        DEPTH = 5
    elif DEPTH < 0.1:
        DEPTH = 0.1

    if AMBIENT_TEMP > 40:
        AMBIENT_TEMP = 40
    elif AMBIENT_TEMP < -40:
        AMBIENT_TEMP = -40

    burnupDF = pd.DataFrame(locals(), index=[0])

    burnupDF.columns = [f'#{col}' for col in burnupDF.columns]
    burnupDF.drop(columns=['#self'], inplace=True)
    burnupDF.drop(columns=['#outBRN'], inplace=True)
    burnupDF = burnupDF.T

    if os.path.exists(os.path.join(outBRN, 'Burnup-In.csv')):
        os.remove(os.path.join(outBRN, 'Burnup-In.csv'))
        os.remove(os.path.join(outBRN, 'Burnup-In.brn'))
    burnupDF.to_csv(os.path.join(outBRN, 'Burnup-In.brn'), sep=' ', header=False)