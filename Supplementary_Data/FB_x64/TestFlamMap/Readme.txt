TestFlamMap

Usage:
TestFlamMap [commandfile]
Where:
        [commandfile] is the path to the command file.

The command file contains command lines for multiple FlamMap runs, each run's command on a seperate line.

Each command expects four parameters, all required
[LCPName] [InputsFileName] [outputDirPath] [outputsType]
Where:
        [LCPName] is the path to the Landscape File
        [InputsFileName] is the path to the FlamMap Inputs File (ASCII Format)
        [outputDirPath] is the path to the output files base name (no extension)
        [outputsType] is the file type for outputs (0 = both, 1 = ASCII grid, 2 = GeoTIFF
        
Example Command File contents:
project.lcp July.input July 1

Using complete paths to all files is encouraged.
So the above example could become:
C:\Data\project.lcp C:\Data\July.input C:\Data\July 1

Multiple commands can be used in the command file, one command per line

e.g.
C:\Data\project.lcp C:\Data\June.input C:\Data\June 1
C:\Data\project.lcp C:\Data\July.input C:\Data\July 1
C:\Data\project.lcp C:\Data\August.input C:\Data\August 1

It is important to note that any path specified in the outputDirPath must exist, TestFlamMap will not create directories.
TestFlamMap attempts to create all outputs, provided base output layers are specified in the inputs file, and projection information is available.

No warranties expressed or implied.
   