TestFSPro Example dataset and Inputs file

Landscape Data:
416lcp.lcp - WFDSS Generated LCP file at 90m resolution
416lcp.prj - Projection information for the LCP. It is in the standard WFDSS Custom projection format.

NOTE: the landscape file and the ignition file need to be in the same datum and projection for use in TestFSPro. 

Ignition Data:
416ign.shp (.dbf, .shx, .prj) is a polygon ignition file based on an IR Perimeter
Projection is in the same WFDSS Albers Projection as the LCP File

TestFSPro Inputs File:
416inputsfile.input  contains all the information to run the simulation.
The user will want to check the following items. 

NumFires: is currently set to 100. This is intended to produce an output in a reasonalble amount of time for illustration purposes. In Reality the number of simulated fires will need to be much higher. In the range 1000-3000 fires at a minimum.

Ignition File Location: Be sure to check the path to the appropriate ignition file location. As distributed, the inputs file is set up to run only from the TestFSPro\SampleData directory.

TestFSPro Usage: 
TestFSpro Runs from the DOS Command Run Window
1. Open the DOS Command Run Window
2. Change Directories to the TestFSPro\SampleData directory. 
3. Run Test FSPro:
TestFSPro Usage:
TestFSPro [LCPName] [InputsFileName] [OutputFileName]
Where:
	[LCPName] is the path to the Landscape File
        [InputsFileName] is the path to the FSPro Inputs Text File (ASCII Format)
        [outputFileName] is the path to the output files base name (no extension)

Alternatively, the RunFSPro.bat batch file can be used to launch the TestFSPro sample run.

All outputs for TestFSPro are written to the TestFSPro\SampleData\Outputs directory.