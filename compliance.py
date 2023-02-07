#!/usr/bin/env python3

from cdo import * # Provides functions for the manipulation of climate data NetCDF files.
import nco
from pathlib import Path # Provides functions for manipulating files.

cdo = Cdo()

# Search for all files with a .nc extension in the current directory.
path = Path('.')
nc_files = list(path.glob('*.nc'))

# Find files with name containing the date range 2000-2009, and split this file into a historical and projected file with historical file having metadata updated.
for nc_file in nc_files:
    if "2000-2009" in nc_file.name:
        nc_experiment = nc_file.name.split("_")[0]
        cdo.selyear("2000/2005", input=nc_file, output="historical.nc")