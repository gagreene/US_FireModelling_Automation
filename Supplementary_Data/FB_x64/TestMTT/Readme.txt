TestMTT

Usage:
TestMTT [commandfile]
Where:
        [commandfile] is the path to the command file.

The command file contains command lines for multiple MTT runs, each run's command on a seperate line.
Each command expects six parameters, all required
[LCPName] [InputsFileName] [IgnitionFileName] [BarrierFileName] [outputDirPath] [outputsType]
Where:
        [LCPName] is the path to the Landscape File
        [InputsFileName] is the path to the MTT Inputs File (ASCII Format)
        [IgnitionFileName] is the path to the Ignition shape File
        [BarrierFileName] is the path to the Barrier shape File (0 if no barrier)
        [outputDirPath] is the path to the output files base name (no extension)
        [outputsType] is the file type for outputs (0 = both, 1 = ASCII grid, 2= GeoTIFF, > 3 = ShapeFile only        

Example Command File contents:
project.lcp July.input July10.shp 0 July10 1

Using complete paths to all files is encouraged.
So the above example could become:
C:\Data\project.lcp C:\Data\July.input C:\Data\July10.shp 0 C:\Data\July10 1

Multiple commands can be used in the command file, one command per line

e.g.
C:\Data\project.lcp C:\Data\July.input C:\Data\July10.shp 0 C:\Data\July10 1
C:\Data\project.lcp C:\Data\July.input C:\Data\July10.shp C:\Data\July09.shp C:\Data\July10 1

It is important to note that any path specified in the outputDirPath must exist, TestMTT will not create directories.
TestMTT attempts to create all MTT and FlamMap outputs, provided base output layers are specified in the inputs file.

No warranties expressed or implied.
   