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
nco.debug = True

# Search for all files with a .nc extension in the current directory.
path = Path('.')
nc_files = list(path.glob('*.nc'))

# Options for renaming historical based output variable files.
opt_historical = [
    ["-h"],
    ["-a" " \'experiment_id\',global,o,c,\'historical\'"],
    ["-a" " \'experiment\',global,o,c,\'historical\'"],
    ["-a" " \'driving_experiment\',global,o,c,\'historical\'"],
    ["-a" " \'driving_experiment_name\',global,o,c,\'historical\'"],
    ["-a" " \'domain\',global,o,c,\'GLB-50i\'"],
    ["-a" " \'comment\',global,o,c,\'GLB-50i\'"],
    ["-a" " \'frequency\',global,o,c,\'day\'"]
]

# Options for renaming experimental based output variable files.
opt_experimental = [
    ["-h"],
    ["-a" " \'domain\',global,o,c,\'GLB-50i\'"],
    ["-a" " \'comment\',global,o,c,\'GLB-50i\'"],
    ["-a" " \'frequency\',global,o,c,\'day\'"]
]

for nc_file in nc_files:
    # Find files with name containing the date range 2000-2009, and split this file into a historical and projected file with historical file having metadata updated.
    if "2000-2009" in nc_file.name:
        nc_historical = nc_file.name.split(".")[0] + ".2000-2005.nc"
        nc_experiment = nc_file.name.split(".")[0] + ".2006-2009.nc"
        cdo.selyear("2000/2005", input=nc_file.name, output=nc_historical)
        cdo.selyear("2006/2009", input=nc_file.name, output=nc_experiment)
        nco.ncatted(input=nc_historical, options = opt_historical, output=nc_historical)
        nco.ncatted(input=nc_experiment, options = opt_experimental, output=nc_experiment)
    # Fix metadata for remaining files.
    if int(nc_file.name.split(".")[1].split("-")[0]) <= 2005:
        print("hist")
        nco.ncatted(input=nc_file.name, options = opt_historical, output=nc_file.name)
    if int(nc_file.name.split(".")[1].split("-")[0]) >= 2006:
        print("exp")
        nco.ncatted(input=nc_file.name, options=opt_experimental, output=nc_file.name)
    
    # Rename and relocate files according to DRS standard.
    nc_headers = nco.ncdump(nc_file.name, h=True)
    print(nc_headers)
    product = nco.ncdump(nc_file.name, h=True, v=True).split("product:")[1].split("")
    print(product)
    