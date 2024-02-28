# -*- coding: utf-8 -*-
"""
Created on Wed Nov  19 11:17:52 2023

@author: Gregory A. Greene
"""
import os
#import glob
import pandas as pd
import arcpy
from arcpy.sa import *
#from arcpy.ia import Max, Sum, Mean

# Checkout ArcGIS Spatial Analyst extension
arcpy.CheckOutExtension('Spatial')


# Function to import CSV as a Pandas Dataframe
def getDF(csv):
    return pd.read_csv(csv, header=0, index_col=False)


# Function to export Pandas Dataframe to CSV
def exportCSV(df, csv):
    if os.path.exists(csv):
        os.remove(csv)
    df.to_csv(csv, sep=',', index=False)
    return

# Function to convert Feature Class to Pandas Dataframe
def table_toDF(in_table, input_fields=None, where_clause=None):
    """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    input fields using an arcpy.da.SearchCursor."""
    OIDFieldName = arcpy.Describe(in_table).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_table)]
    data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]
    fc_dataframe = pd.DataFrame(data, columns=final_fields)
    fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)
    return fc_dataframe

# Check if field exists in ArcGIS feature class
def fieldExists(feature_class, field_name):
    if field_name in [field.name for field in arcpy.ListFields(feature_class)]:
        return True
    else:
        return False


### LISTS AND DICTIONARIES
season_list = ['Spring', 'Summer', 'Fall']
percentile_list = [90, 95, 99]
asset_list = ['BESSFacility', 'Cabling', 'Capacitor', 'CellTower', 'ControlBox', 'Insulator', 'Pole',
              'PrimaryConductor', 'PrimaryConductorUG_RiserPole', 'PrimarySwitch', 'Recloser', 'Regulator',
              'SwitchCubicle', 'Transformer']
criticality_list = ['Accessibility', 'Cost', 'CriticalCustomer', 'Difficulty', 'NonCritCustomer', 'SCADA']
vulnerability_list = ['DirectFlameContact', 'EmberPotential', 'HeatExposure', 'SmokeAshPotential']
heatSensitive_list = ['Aluminum+PCB', 'Epoxy Resin', 'HDPE for riser (cable LLDPE)', 'LDPE', 'Lexan',
                      'Polymer (polyethylene)', 'Wood']
rasterCalculationType_list = ['MAXIMUM', 'MEAN', 'RANGE']


### MODELLING SWITCHES
generateScoreRanksAndRasters = False
generateAssetScoreRanksAndRasters = True
changeNullToZero = True


### GET PATHS TO GDBs, FOLDERS, AND DATASETS
scratch_gdb = r'E:\FortisAB_1567_4\scratch.gdb'
modelling_gdb = r'S:\1567\4\03_MappingAnalysisData\02_Data\01_Base_Data\modelling_data.gdb'
rasterGrid_points = os.path.join(modelling_gdb, 'Modelling_RasterGrid_Points')
modelling_folder = r'S:\1567\4\03_MappingAnalysisData\02_Data\05_FBP_Modelling_Data'
wx_regions = os.path.join(modelling_folder, 'wxRegions.tif')
base_folder = os.path.join(modelling_folder, 'Base')
vulnerability_folder = r'S:\1567\4\03_MappingAnalysisData\02_Data\07_Vulnerability_Analysis'
critVul_scoring_folder = r'S:\1567\4\03_MappingAnalysisData\02_Data\08_Criticality_Vulnerability_Scoring'
asset_gdb = os.path.join(critVul_scoring_folder, 'Model_Asset_Inputs.gdb')
criticalityInput_gdb = os.path.join(critVul_scoring_folder, 'CriticalityScoring_InputDatasets.gdb')
criticalityVulnerability_noBurns_gdb = os.path.join(critVul_scoring_folder,
                                                    'CriticalityVulnerabilityScoring_NoBurns.gdb')
criticalityVulnerability_withBurns_gdb = os.path.join(critVul_scoring_folder,
                                                      'CriticalityVulnerabilityScoring_WithBurns.gdb')
criticalityVulnerability_noBurns_final_gdb = os.path.join(critVul_scoring_folder,
                                                          'CriticalityVulnerabilityScoring_NoBurns_Final.gdb')
criticalityVulnerability_withBurns_final_gdb = os.path.join(critVul_scoring_folder,
                                                            'CriticalityVulnerabilityScoring_WithBurns_Final.gdb')
resultsFolder = os.path.join(critVul_scoring_folder, '_Results')
results_noBurns_Folder = os.path.join(resultsFolder, 'No_Burns')
results_withBurns_Folder = os.path.join(resultsFolder, 'No_Burns')
assetLevelFolder = os.path.join(resultsFolder, 'Asset_Level')
assetLevelScores_noBurns_folder = os.path.join(assetLevelFolder, 'No_Burns')
assetLevelScores_withBurns_folder = os.path.join(assetLevelFolder, 'With_Burns')
categoryScoresFolder = os.path.join(resultsFolder, 'Category_Scores')
categoryScores_noBurns_folder = os.path.join(categoryScoresFolder, 'No_Burns')
categoryScores_withBurns_folder = os.path.join(categoryScoresFolder, 'With_Burns')
categoryIntermediateScoresFolder = os.path.join(categoryScoresFolder, 'Intermediate')
categoryIntermediateScores_noBurns_folder = os.path.join(categoryIntermediateScoresFolder, 'No_Burns')
categoryIntermediateScores_withBurns_folder = os.path.join(categoryIntermediateScoresFolder, 'With_Burns')
assetScoresFolder = os.path.join(resultsFolder, 'Asset_Scores')
assetScores_noBurns_folder = os.path.join(categoryScoresFolder, 'No_Burns')
assetScores_withBurns_folder = os.path.join(categoryScoresFolder, 'With_Burns')
assetIntermediateScoresFolder = os.path.join(assetScoresFolder, 'Intermediate')
assetIntermediateScores_noBurns_folder = os.path.join(assetIntermediateScoresFolder, 'No_Burns')
assetIntermediateScores_withBurns_folder = os.path.join(assetIntermediateScoresFolder, 'With_Burns')
totalScores_folder = os.path.join(resultsFolder, 'Total_Scores')
totalScores_noBurns_folder = os.path.join(totalScores_folder, 'No_Burns')
totalScores_withBurns_folder = os.path.join(totalScores_folder, 'With_Burns')

# Get raster and feature class input datasets
wx_region_ras = Raster(wx_regions)

# Set ArcGIS environment parameters
arcpy.env.workspace = scratch_gdb  # Set ArcGIS workspace to scratch GDB
arcpy.env.overwriteOutput = True
arcpy.env.parallelProcessingFactor = '100%'
arcpy.env.outputCoordinateSystem = wx_region_ras
arcpy.env.extent = arcpy.Describe(wx_region_ras).extent
arcpy.env.snapRaster = wx_region_ras
arcpy.env.cellSize = wx_region_ras

if generateScoreRanksAndRasters:
    print('\nCreating Score Ranks and Rasters')

    # Get list of total score fields
    print('\tGenerating list of Total Score fields')
    scoreFields_list = []
    for percentile in percentile_list:
        for season in season_list:
            scoreFields_list += [f'Total_10x_SCORE_{percentile}_{season}']

    # Get dictionary of score ranks with value ranges
    print('\tGenerating dictionary of score ranks with value ranges')
    ranks_dict = {
        'LOW': [0, 21.25],
        'MODERATE': [21.25, 42.5],
        'HIGH': [42.5, 63.75],
        'VERY HIGH': [63.75, 85]
    }

    print('\tCreating empty "No Burns" and "With Burns" score rank dataframes')
    #noBurnsDF_assets = pd.DataFrame(columns=scoreFields_list, index=asset_list)
    #withBurnsDF_assets = pd.DataFrame(columns=scoreFields_list, index=asset_list)
    totalDF_noBurns = pd.DataFrame(columns=scoreFields_list, index=list(ranks_dict.keys()))
    totalDF_withBurns = pd.DataFrame(columns=scoreFields_list, index=list(ranks_dict.keys()))

    print('\tImporting "No Burns" Assets_Merged feature class')
    arcpy.MakeFeatureLayer_management(
        in_features=os.path.join(criticalityVulnerability_noBurns_final_gdb, 'Assets_Merged'),
        out_layer='NoBurns_AssetsMerged')

    print('\tImporting "With Burns" Assets_Merged feature class')
    arcpy.MakeFeatureLayer_management(
        in_features=os.path.join(criticalityVulnerability_withBurns_final_gdb, 'Assets_Merged'),
        out_layer='WithBurns_AssetsMerged')

    print('\tPulling data from asset merged feature classes and adding to score rank dataframes')
    for field in scoreFields_list:
        print(f'\n\t\tProcessing {field} data')
        for rank in list(ranks_dict.keys()):
            print(f'\t\t\tProcessing {rank} score rank')

            # NO BURNS DATA
            print(f'\t\t\t\tProcessing "No Burns" data')
            print(f'\t\t\t\t\tSelecting features')
            sel_feats = arcpy.SelectLayerByAttribute_management(
                in_layer_or_view='NoBurns_AssetsMerged',
                selection_type='NEW_SELECTION',
                where_clause=f'"{field}" > {ranks_dict.get(rank)[0]} And "{field}" <= {ranks_dict.get(rank)[1]} '
            )
            print(f'\t\t\t\t\tGetting feature count')
            totalDF_noBurns.loc[rank, field] = arcpy.GetCount_management('NoBurns_AssetsMerged')
            print(f'\t\t\t\t\tCreating Rank Score raster')
            arcpy.PointToRaster_conversion(
                in_features=sel_feats,
                value_field=f'{field}',
                out_rasterdataset='TempRas_RankScore',
                cell_assignment='COUNT'
            )
            temp_path = os.path.join(totalScores_noBurns_folder, f'{rank}_{field}.tif')
            temp_ras = Con(IsNull('TempRas_RankScore'), 0, 'TempRas_RankScore')
            temp_ras.save(temp_path)
            print(f'\t\t\t\t\t\tCreating Aggregate Rank Score raster')
            agg_raster = Aggregate(
                in_raster='TempRas_RankScore',
                cell_factor=10,
                aggregation_type='SUM',
                extent_handling='EXPAND',
                ignore_nodata='DATA'
            )
            agg_raster = Con(IsNull(agg_raster), 0, agg_raster)
            print(f'\t\t\t\t\t\tSaving dataset')
            agg_raster.save(
                os.path.join(totalScores_noBurns_folder,
                             f'Aggregated_{rank}_{field}.tif')
            )
            # Clear selection
            print(f'\t\t\t\t\tClearing selected features')
            arcpy.SelectLayerByAttribute_management(sel_feats,
                                                    'CLEAR_SELECTION')


            # WITH BURNS DATA
            print(f'\t\t\t\tProcessing "With Burns" data')
            print(f'\t\t\t\t\tSelecting features')
            sel_feats = arcpy.SelectLayerByAttribute_management(
                in_layer_or_view='WithBurns_AssetsMerged',
                selection_type='NEW_SELECTION',
                where_clause=f'"{field}" > {ranks_dict.get(rank)[0]} And "{field}" <= {ranks_dict.get(rank)[1]} '
            )
            print(f'\t\t\t\t\tGetting feature count')
            totalDF_withBurns.loc[rank, field] = arcpy.GetCount_management('WithBurns_AssetsMerged')
            print(f'\t\t\t\t\tCreating Rank Score raster')
            arcpy.PointToRaster_conversion(
                in_features=sel_feats,
                value_field=f'{field}',
                out_rasterdataset='TempRas_RankScore',
                cell_assignment='COUNT'
            )
            temp_path = os.path.join(totalScores_withBurns_folder, f'{rank}_{field}.tif')
            temp_ras = Con(IsNull('TempRas_RankScore'), 0, 'TempRas_RankScore')
            temp_ras.save(temp_path)
            print(f'\t\t\t\t\t\tCreating Aggregate Rank Score raster')
            agg_raster = Aggregate(
                in_raster='TempRas_RankScore',
                cell_factor=10,
                aggregation_type='SUM',
                extent_handling='EXPAND',
                ignore_nodata='DATA'
            )
            agg_raster = Con(IsNull(agg_raster), 0, agg_raster)
            print(f'\t\t\t\t\t\tSaving dataset')
            agg_raster.save(
                os.path.join(totalScores_withBurns_folder,
                             f'Aggregated_{rank}_{field}.tif')
            )
            # Clear selection
            print(f'\t\t\t\t\tClearing selected features')
            arcpy.SelectLayerByAttribute_management(sel_feats,
                                                    'CLEAR_SELECTION')

    print('\tSaving "No Burns" score rank dataframe to CSV')
    exportCSV(totalDF_noBurns, os.path.join(totalScores_folder, 'NoBurns_TotalScoresTable.csv'))
    print('\tSaving "With Burns" score rank dataframe to CSV')
    exportCSV(totalDF_withBurns, os.path.join(totalScores_folder, 'WithBurns_TotalScoresTable.csv'))



if generateAssetScoreRanksAndRasters:
    print('\nCreating Asset Score Ranks and Rasters')

    # Get list of total score fields
    print('\tGenerating list of Total Score fields')
    scoreFields_list = []
    for percentile in percentile_list:
        for season in season_list:
            scoreFields_list += [f'Total_10x_SCORE_{percentile}_{season}']

    # Get dictionary of score ranks with value ranges
    print('\tGenerating dictionary of score ranks with value ranges')
    ranks_dict = {
        'LOW': [0, 21.25],
        'MODERATE': [21.25, 42.5],
        'HIGH': [42.5, 63.75],
        'VERY HIGH': [63.75, 85]
    }

    for asset in asset_list:
        assetRank_list = [[asset, rank] for rank in list(ranks_dict.keys())]

    print('\tCreating empty "No Burns" and "With Burns" score rank dataframes')
    #noBurnsDF_assets = pd.DataFrame(columns=scoreFields_list, index=asset_list)
    #withBurnsDF_assets = pd.DataFrame(columns=scoreFields_list, index=asset_list)
    totalDF_noBurns = pd.DataFrame(columns=scoreFields_list, index=assetRank_list)
    totalDF_withBurns = pd.DataFrame(columns=scoreFields_list, index=assetRank_list)

    print('\tImporting "No Burns" Assets_Merged feature class')
    arcpy.MakeFeatureLayer_management(
        in_features=os.path.join(criticalityVulnerability_noBurns_final_gdb, 'Assets_Merged'),
        out_layer='NoBurns_AssetsMerged')

    print('\tImporting "With Burns" Assets_Merged feature class')
    arcpy.MakeFeatureLayer_management(
        in_features=os.path.join(criticalityVulnerability_withBurns_final_gdb, 'Assets_Merged'),
        out_layer='WithBurns_AssetsMerged')

    print('\tPulling data from asset merged feature classes and adding to score rank dataframes')
    for field in scoreFields_list:
        print(f'\n\t\tProcessing {field} data')
        for asset in asset_list:
            print(f'\t\t\tProcessing {asset} asset')
            for rank in list(ranks_dict.keys()):
                print(f'\t\t\t\tProcessing {rank} score rank')

                # NO BURNS DATA
                print(f'\t\t\t\t\tProcessing "No Burns" data')
                print(f'\t\t\t\t\t\tSelecting features')
                sel_feats = arcpy.SelectLayerByAttribute_management(
                    in_layer_or_view='NoBurns_AssetsMerged',
                    selection_type='NEW_SELECTION',
                    where_clause=f'"ASSET_TYPE" = {asset} And '
                                 f'"{field}" > {ranks_dict.get(rank)[0]} And "{field}" <= {ranks_dict.get(rank)[1]}'
                )
                print(f'\t\t\t\t\t\tGetting feature count')
                feature_count = arcpy.GetCount_management('NoBurns_AssetsMerged')
                totalDF_noBurns.loc[[asset, rank], field] = feature_count
                if feature_count > 0:
                    print(f'\t\t\t\t\t\tCreating Rank Score raster')
                    arcpy.PointToRaster_conversion(
                        in_features=sel_feats,
                        value_field=f'{field}',
                        out_rasterdataset='TempRas_RankScore',
                        cell_assignment='COUNT'
                    )
                    temp_path = os.path.join(totalScores_noBurns_folder, 'Assets', f'{rank}_{asset}_{field}.tif')
                    temp_ras = Con(IsNull('TempRas_RankScore'), 0, 'TempRas_RankScore')
                    temp_ras.save(temp_path)
                    print(f'\t\t\t\t\t\t\tCreating Aggregate Rank Score raster')
                    agg_raster = Aggregate(
                        in_raster='TempRas_RankScore',
                        cell_factor=10,
                        aggregation_type='SUM',
                        extent_handling='EXPAND',
                        ignore_nodata='DATA'
                    )
                    agg_raster = Con(IsNull(agg_raster), 0, agg_raster)
                    print(f'\t\t\t\t\t\t\tSaving dataset')
                    agg_raster.save(
                        os.path.join(totalScores_noBurns_folder, 'Assets',
                                     f'Aggregated_{rank}_{asset}_{field}.tif')
                    )
                    # Clear selection
                    print(f'\t\t\t\t\t\tClearing selected features')
                    arcpy.SelectLayerByAttribute_management(sel_feats,
                                                            'CLEAR_SELECTION')


                # WITH BURNS DATA
                print(f'\t\t\t\t\tProcessing "With Burns" data')
                print(f'\t\t\t\t\t\tSelecting features')
                sel_feats = arcpy.SelectLayerByAttribute_management(
                    in_layer_or_view='WithBurns_AssetsMerged',
                    selection_type='NEW_SELECTION',
                    where_clause=f'"ASSET_TYPE" = {asset} And '
                                 f'"{field}" > {ranks_dict.get(rank)[0]} And "{field}" <= {ranks_dict.get(rank)[1]} '
                )
                print(f'\t\t\t\t\t\tGetting feature count')
                feature_count = arcpy.GetCount_management('WithBurns_AssetsMerged')
                totalDF_withBurns.loc[[asset, rank], field] = feature_count
                if feature_count > 0:
                    print(f'\t\t\t\t\t\tCreating Rank Score raster')
                    arcpy.PointToRaster_conversion(
                        in_features=sel_feats,
                        value_field=f'{field}',
                        out_rasterdataset='TempRas_RankScore',
                        cell_assignment='COUNT'
                    )
                    temp_path = os.path.join(totalScores_withBurns_folder, 'Assets', f'{rank}_{asset}_{field}.tif')
                    temp_ras = Con(IsNull('TempRas_RankScore'), 0, 'TempRas_RankScore')
                    temp_ras.save(temp_path)
                    print(f'\t\t\t\t\t\t\tCreating Aggregate Rank Score raster')
                    agg_raster = Aggregate(
                        in_raster='TempRas_RankScore',
                        cell_factor=10,
                        aggregation_type='SUM',
                        extent_handling='EXPAND',
                        ignore_nodata='DATA'
                    )
                    agg_raster = Con(IsNull(agg_raster), 0, agg_raster)
                    print(f'\t\t\t\t\t\t\tSaving dataset')
                    agg_raster.save(
                        os.path.join(totalScores_withBurns_folder, 'Assets',
                                     f'Aggregated_{rank}_{asset}_{field}.tif')
                    )
                    # Clear selection
                    print(f'\t\t\t\t\t\tClearing selected features')
                    arcpy.SelectLayerByAttribute_management(sel_feats,
                                                            'CLEAR_SELECTION')

    print('\tSaving "No Burns" score rank dataframe to CSV')
    totalDF_noBurns.reset_index(inplace=True)
    exportCSV(totalDF_noBurns, os.path.join(totalScores_folder, 'NoBurns_TotalAssetScoresTable.csv'))
    print('\tSaving "With Burns" score rank dataframe to CSV')
    totalDF_withBurns.reset_index(inplace=True)
    exportCSV(totalDF_withBurns, os.path.join(totalScores_folder, 'WithBurns_TotalAssetScoresTable.csv'))


if changeNullToZero:
    print('\nCreating Score Ranks and Rasters')

    # Get list of total score fields
    print('\tGenerating list of Total Score fields')
    scoreFields_list = []
    for percentile in percentile_list:
        for season in season_list:
            scoreFields_list += [f'Total_10x_SCORE_{percentile}_{season}']

    # Get dictionary of score ranks with value ranges
    print('\tGenerating dictionary of score ranks with value ranges')
    ranks_dict = {
        'LOW': [0, 21.25],
        'MODERATE': [21.25, 42.5],
        'HIGH': [42.5, 63.75],
        'VERY HIGH': [63.75, 85]
    }

    for field in scoreFields_list:
        print(f'\n\tProcessing {field} data')
        for rank in list(ranks_dict.keys()):
            print(f'\t\tProcessing {rank} score rank')
            # NO BURNS DATA
            print(f'\t\t\tProcessing "No Burns" data')
            temp_path = os.path.join(totalScores_noBurns_folder, f'Aggregated_{rank}_{field}.tif')
            temp_ras = Raster(temp_path)
            temp_ras = Con(IsNull(temp_ras), 0, temp_ras)
            temp_ras.save(os.path.join(totalScores_noBurns_folder, 'Reprocessed', f'Aggregated_{rank}_{field}.tif'))
            # WITH BURNS DATA
            print(f'\t\t\tProcessing "With Burns" data')
            temp_path = os.path.join(totalScores_withBurns_folder, f'Aggregated_{rank}_{field}.tif')
            temp_ras = Raster(temp_path)
            temp_ras = Con(IsNull(temp_ras), 0, temp_ras)
            temp_ras.save(os.path.join(totalScores_withBurns_folder, 'Reprocessed', f'Aggregated_{rank}_{field}.tif'))
