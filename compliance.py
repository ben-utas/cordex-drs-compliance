#!/usr/bin/env python3

from cdo import * # Provides functions for the manipulation of climate data NetCDF files.
from nco import Nco # Provides functions for the manipulation of general NetCDF files.
from nco.custom import Atted
from pathlib import Path # Provides functions for manipulating files.

output_variables = [
    "epanave", "hurs", "pr", "ps", "rh", "rnetave", "soilt", "tas"
]

invariant_variables = [
    "grid", "he", "orog", "sftlf", "sigmu", "vegt"
]

cdo = Cdo()
nco = Nco()

# Search for all files with a .nc extension in the current directory.
path = Path('.')
nc_files = list(path.glob('*.nc'))

# Find files with name containing the date range 2000-2009, and split this file into a historical and projected file with historical file having metadata updated.
for nc_file in nc_files:
    if "2000-2009" in nc_file.name:
        nc_historical = nc_file.name.split("_")[0] + "2000-2005.nc"
        nc_experiment = nc_file.name.split("_")[0] + "2006-2009.nc"
        cdo.selyear("2000/2005", input=nc_file, output=nc_historical)
        cdo.selyear("2006/2009", input=nc_file, output=nc_experiment)
        nco.ncrename
