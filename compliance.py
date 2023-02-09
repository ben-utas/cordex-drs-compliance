#!/usr/bin/env python3

import argparse # Provides functions for parsing command line arguments.
from pathlib import Path # Provides functions for manipulating files.

from cdo import * # Provides functions for the manipulation of climate data NetCDF files.
from nco import Nco # Provides functions for the manipulation of general NetCDF files.
from nco.custom import Atted # Provides functions for the manipulation of NetCDF attributes.

parser = argparse.ArgumentParser(
    prog="CORDEX Compliance Enforcer and Path Builder",
    description="Fix metadata and rename files to comply with CORDEX DRS standard."
)

parser.add_argument(
    '-d', '--destination',
    help='Destination directory for output files.',
    type=Path,
    default=Path('.')
)

target = parser.parse_args().destination

if not target.exists() and not target.is_dir():
    print("Destination directory does not exist.")
    exit()

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

# Options for renaming historical based output variable files.
opt_historical = [
    Atted("m", "experiment_id", "global attributes", "historical"),
    Atted("m", "experiment", "global attributes", "historical"),
    Atted("m", "driving_experiment", "global attributes", "historical"),
    Atted("m", "driving_experiment_name", "global attributes", "historical"),
    Atted("m", "domain", "global attributes", "GLB-50i"),
    Atted("m", "comment", "global attributes", "GLB-50i"),
    Atted("m", "frequency", "global attributes", "day")
]

# Options for renaming experimental based output variable files.
opt_experimental = [
    Atted("m", "domain", "global attributes", "GLB-50i"),
    Atted("m", "comment", "global attributes", "GLB-50i"),
    Atted("m", "frequency", "global attributes", "day")
]


for nc_file in nc_files:
    # Find files with name containing the date range 2000-2009, and split this file into a historical and projected file with historical file having metadata updated.
    if "2000-2009" in nc_file.name:
        nc_historical = nc_file.name.split(".")[0] + ".2000-2005.nc"
        nc_experiment = nc_file.name.split(".")[0] + ".2006-2009.nc"
        cdo.selyear("2000/2005", input=nc_file, output=nc_historical)
        cdo.selyear("2006/2009", input=nc_file, output=nc_experiment)
        nco.ncatted(opt_historical, input=nc_historical)
        nco.ncatted(opt_experimental, input=nc_experiment)
    # Fix metadata for remaining files.
    if int(nc_file.name.split(".")[1].split("-")[0]) < 2000:
        nco.ncatted(opt_historical, input=nc_file)
    if int(nc_file.name.split(".")[1].split("-")[0]) > 2009:
        nco.ncatted(opt_experimental, input=nc_file)
    
    # Rename and relocate files according to DRS standard.
    nc_headers = nco.ncdump(nc_file, h=True)
    print(nc_headers)
    product = nco.ncdump(nc_file, h=True, v=True).split("product:")[1].split("")
    print(product)
    