__author__ = ['Gregory A. Greene, map.n.trowel@gmail.com']

import os
import subprocess
import rasterio as rio
from rasterio import shutil

def jPath(*args):
    path = ''
    for x in args:
        path = os.path.join(path, f'{x}')
    return path


def makeLCP(latitude=None, lcpFile=None, elev=None, slope=None, aspect=None, fbfm=None,
                cc=None, ch=None, cbh=None, cbd=None):

    if None in [latitude, lcpFile, elev, slope, aspect, fbfm, cc, ch, cbh, cbd]:
        raise Exception('Missing at least one required input to generate the LCP file.')

    # ### GET PATH TO lcpmake.exe
    bin_path = '.\\Supplementary_Data\\FB_x64\\bin'
    lcpmake_path = jPath(bin_path, 'lcpmake.exe')

    # ###Run LCP maker executable
    makeLCP = f'{lcpmake_path} -latitude {latitude} -landscape {lcpFile} -elevation {elev} \
      -slope {slope} -aspect {aspect} -fuel {fbfm} -cover {cc} -height {ch} -base {cbh} \
      -density {cbd}'
    buildLCP = subprocess.run(
        makeLCP,
        capture_output=True,
        text=True
    )
    print(f'\n{buildLCP.stdout}')
    print('\nLandscape file creation complete')

    return


def generateLCP(lcpFile=None, elev_path=None, slope_path=None, aspect_path=None,
                fbfm_path=None, cc_path=None, ch_path=None, cbh_path=None, cbd_path=None):
    elev_ras = rio.open(elev_path, 'r+')
    elev_array = elev_ras.read(1, masked=True)

    slope_ras = rio.open(slope_path, 'r+')
    slope_array = slope_ras.read(1, masked=True)

    aspect_ras = rio.open(aspect_path, 'r+')
    aspect_array = aspect_ras.read(1, masked=True)

    fbfm_ras = rio.open(fbfm_path, 'r+')
    fbfm_array = fbfm_ras.read(1, masked=True)

    cc_ras = rio.open(cc_path, 'r+')
    cc_array = cc_ras.read(1, masked=True)

    ch_ras = rio.open(ch_path, 'r+')
    ch_array = ch_ras.read(1, masked=True)

    cbh_ras = rio.open(cbh_path, 'r+')
    cbh_array = cbh_ras.read(1, masked=True)

    cbd_ras = rio.open(cbd_path, 'r+')
    cbd_array = cbd_ras.read(1, masked=True)

    file_list = [elev_array, slope_array, aspect_array, fbfm_array, cc_array, ch_array, cbh_array, cbd_array]

    out_meta = elev_ras.meta.copy()
    out_meta.update({'count': 8,
                     'nodata': -999})

    shutil.copyfiles(elev_ras.name, lcpFile)

    with rio.open(lcpFile, 'w', **out_meta) as dest:
        for band_nr, src in enumerate(file_list, start=1):
            dest.write(src, band_nr)
        dest.close()
    return

def main(year):
    #latitude = 49.59  # center of study area (used to generate LCP file and calculate burn period (when not pre-defined))

    pool_path = r'S:\1041\8\03_MappingAnalysisData\02_Data\01_Base_Data\CBM_DataFromFlor\PoolsAndFuelModels'
    topo_path = jPath(pool_path, '_Topo_Data')
    fuel_path = jPath(pool_path, '_FlamMap_Data')
    lcp_path = jPath(pool_path, '_LCP_Data')
    out_lcp = jPath(lcp_path, f'{year}_LCP.tif')

    elev_path = jPath(topo_path, 'elevation.tif')
    slope_path = jPath(topo_path, 'slope.tif')
    aspect_path = jPath(topo_path, 'aspect.tif')
    fbfm_path = jPath(fuel_path, f'{year}_FBFM.tif')
    cc_path = jPath(fuel_path, f'{year}_CC.tif')
    ch_path = jPath(fuel_path, f'{year}_CH.tif')
    cbh_path = jPath(fuel_path, f'{year}_CBH.tif')
    cbd_path = jPath(fuel_path, f'{year}_CBD.tif')

    """makeLCP(latitude=latitude, lcpFile=outLCP,
            elev=elev, slope=slope, aspect=aspect,
            fbfm=fbfm, cc=cc, ch=ch, cbh=cbh, cbd=cbd)"""

    generateLCP(lcpFile=out_lcp, elev_path=elev_path, slope_path=slope_path, aspect_path=aspect_path,
                fbfm_path=fbfm_path, cc_path=cc_path, ch_path=ch_path, cbh_path=cbh_path, cbd_path=cbd_path)


if __name__ == '__main__':
    for year in range(1990, 1991):
        main(year=year)
