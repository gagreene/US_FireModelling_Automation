__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import os
import subprocess
import time
import FOFEM
import numpy as np
import pandas as pd

# SWITCHES
calcMortality = False
calcConsumption = True

fofem_fields = [
    '# PlotId',	'Litter', 'wfl1 Hour', 'wfl10 Hour', 'wfl10 Hour', 'Moisture', 'wfl100 Hour',
    'wfl3-6S', 'wfl6-9S', 'wfl9-20S', 'wfl20plusS', 'wfl3-6R', 'wfl6-9R', 'wfl9-20R', 'wfl20plusR',
    'wfl1000HourMoisture', 'Duff', 'DuffMoisture', 'DuffDepth', 'Herbaceous', 'Shrub', 'CrownFoliage',
    'CrownBranch', 'PercentCrownBurned', 'Region', 'CoverGroup', 'Season', 'FuelCategory',
    'SoilFamily', 'SoilMoisture', 'LitterLoad_ConsumEq1', 'PctDuff_ConsumEq2', 'DuffDepth_ConsumEq3',
    'MSE_ConsumEq4', 'Herb_ConsumEq5', 'Shrub_ConsumEq6'
]
fofemCnsmResults = []

### FOFEM Fuel Consumption & Emissions Modelling
if calcConsumption:
    ## Calculate midflame windspeed
    midFlameWS = FOFEM.getMidflameWS(ws=row[plotWsIndex],
                                     cc=row[plotCCIndex]/100,
                                     ht=row[plotSHtIndex],
                                     cbh=row[plotCCP_FSGIndex],
                                     units='SI')

    ## Generate a Burnup-In.brn file with current fire behavior and weather inputs
    FOFEM.genBurnupInFile(outFolder,
                          INTENSITY=round(ehfi, 2),
                          WINDSPEED=round(midFlameWS, 2),
                          AMBIENT_TEMP=round(row[plotTempIndex], 2)
                          )

    ## Finalize FOFEM consumed emissions dataset & run model
    cnsmResults = [np.nan] * len(plotFofCnsmIndices)
    # Check if plot is in consumeDF
    consPlotDF = consumeDF.loc[consumeDF['# PlotId'] == row[plotIdIndex]].copy()
    if not consPlotDF.empty:
        # If plot is in consumeDF...
        # Add percent crown burned to FOFEM consumed emissions csv
        consPlotDF['PercentCrownBurned'] = fbpCF_output[2] * 100
        consPlotDF['PercentCrownBurned'] = consPlotDF.PercentCrownBurned.fillna(0)
        consPlotDF['PercentCrownBurned'] = consPlotDF.PercentCrownBurned.apply(np.int64)
        consPlotDF.to_csv(fofemConsume_CSV_inTemp, index=False, sep=',')

        # Add switches to FOFEM consumed emissions csv
        addLine_toCSV(fofemConsume_CSV_inTemp, ['#1k-SizeClass'], 0)
        addLine_toCSV(fofemConsume_CSV_inTemp, ['#ConsumptionEquation'], 1)
        addLine_toCSV(fofemConsume_CSV_inTemp, ['#BurnUpFile Burnup-In.brn'], 2)

        # Run FOFEM Consumed Emissions Modelling
        os.chdir(r'C:\Program Files (x86)\FOFEM6.7')
        fofCon = subprocess.Popen(
            ['fof_gui',
             'S',
             fofemConsume_CSV_inTemp,
             f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Out.csv',
             f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Run.csv',
             f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Err.txt'],
            stdout=subprocess.PIPE)
        # out, err = fofCon.communicate()
        # print(out)
        # Wait until consumed emissions modelling output is generated
        while not os.path.exists(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Out.csv'):
            time.sleep(1)

        # Extract model results from the modelling output as a list
        with open(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Out.csv', newline='') as f:
            reader = CSV.reader(f)
            consData = list(reader)
        #print(consData)
        if consData:
            cnsmResults = consData[0][1:]
        else:
            cnsmResults = [0] * len(plotFofCnsmIndices)

        # Delete FOFEM Consumed Emissions modelling output data
        if os.path.exists(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Out.csv'):
            os.remove(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Out.csv')
        if os.path.exists(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Run.csv'):
            os.remove(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Run.csv')
        if os.path.exists(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Err.txt'):
            os.remove(f'{outFolder}\\fofemConsumedEmissionsDF_Temp-Err.txt')

    ## Append fofem consumed emissions modelling results to results list
    fofemCnsmResults.append(cnsmResults)
    allWxList.extend(cnsmResults)
