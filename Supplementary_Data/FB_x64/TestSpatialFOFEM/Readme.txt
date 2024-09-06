SpatialFOFEM 

Release date 5/11/2023

NOTE: For proper running of SpatialFOFEM, please run the SetEnv.bat file in the same command window as running TestSpatialFOFEM. This will ensure GDAL_DATA and PROJ_LIB environment variables are set correctly, and SpatialFOFEM can read/write spatial reference system information correctly.

SpatialFOFEM uses FCCS fuel definitions to run FOFEM on cells across a landscape.

Additionally, users may supply definitions for their own fuel codes, or redefine (tweak) existing FCCS code fuel beds.

SpatialFOFEM allows for input of 10 hour, 1000 hour, and duff fuel moisture grids. 

See SpatialFOFEM Inputs File.pdf for a description of switches available for SpatialFOFEM.

The application TestSpatialFOFEM is included to test the functionality of SpatialFOFEM
TestSpatialFOFEM reads an input file, runs SpatialFOFEM, and outputs each individual selected output to a GeoTIFF file. Further, all selected outputs are also written to a single GeoTIFF file.
A general statistics csv and warnings csv is also produced for each run.

Sample data has been provided. The four samples available are:

RunSpatialFOFEM.bat, which runs SpatialFOFEM on data downloaded direct from the Landfire rest service using FlamMap's GetLandscape program. Further, it uses 10 hour and 100 hour fuel moisture grids generated from FlamMap for the area in question. This example selects every available SpatialFOFEM output.

RunSpatialFOFEMEmissionTotalFuel.bat runs SpatialFOFEM on the same dataset, but only outputs emissions and total fuel and carbon outputs.

RunClipTest.bat runs SpatialFOFEM on the same dataset. This sample demonstrates the use of a shapefile as a mask for calculations.

RunSpatialFofemMortality.bat runs the mortality section of SpatialFOFEM using a TreeMap2016 TreeList ID layer for the same area as the previous samples. The TreeList ID layer was created using TreeListClip, available in Fire Modeling Services Framework


Please note that the sample input files are set up to run regardless of extraction location, in a relative directory structure. In practice it is best to put complete paths to files referenced in the inputs files,
entering the arguments on the command line instead of running in a batch file.

