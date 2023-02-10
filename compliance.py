#!/usr/bin/env python3

import argparse # Provides functions for parsing command line arguments.
import subprocess # Provides functions for running shell commands.
from pathlib import Path # Provides functions for manipulating files.

from cdo import * # Provides functions for the manipulation of climate data NetCDF files.

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

# Search for all files with a .nc extension in the current directory.
path = Path('.')
nc_files = list(path.glob('*.nc'))

# Command for renaming historical based output variable files.
opt_historical = (
    "ncatted -O -h " +
    "-a experiment_id,global,o,c,historical " +
    "-a experiment,global,o,c,historical " +
    "-a driving_experiment,global,o,c,historical " +
    "-a driving_experiment_name,global,o,c,historical " +
    "-a domain,global,o,c,GLB-50i " +
    "-a comment,global,o,c,GLB-50i " +
    "-a frequency,global,o,c,day "
)

# Command for renaming experimental based output variable files.
opt_experimental = (
    "ncatted -O -h " +
    "-a domain,global,o,c,GLB-50i " +
    "-a comment,global,o,c,GLB-50i " +
    "-a frequency,global,o,c,day "
)

def relocate(nc_file: Path):
    """Rename and relocate files according to DRS standard.

    Args:
        nc_file (Path): Path to NetCDF file to be renamed and relocated.
    """
    nc_headers = subprocess.run("ncdump -h " + nc_file.name, stdout=subprocess.PIPE, shell=True)
    nc_headers = nc_headers.stdout.decode("utf-8").split('\n')
    variable_name = nc_file.name.split("_")[0]
    # Find the string in nc_headers that contains each variable.
    for s in nc_headers:
        if "product" in s:
            product = s.split("\"")[1]
        if "domain" in s:
            domain = s.split("\"")[1]
        if "institution" in s:
            institution = s.split("\"")[1]

for nc_file in nc_files:
    # Find files with name containing the date range 2000-2009, and split this file into a historical and projected file with historical file having metadata updated.
    if "2000-2009" in nc_file.name:
        nc_historical = nc_file.name.split(".")[0] + ".2000-2005.nc"
        nc_experiment = nc_file.name.split(".")[0] + ".2006-2009.nc"
        cdo.selyear("2000/2005", input=nc_file.name, output=nc_historical)
        cdo.selyear("2006/2009", input=nc_file.name, output=nc_experiment)
        subprocess.run(opt_historical + nc_historical, shell=True)
        subprocess.run(opt_experimental + nc_experiment, shell=True)
        relocate(path.glob(nc_historical)[0])
        relocate(path.glob(nc_experiment)[0])
    # Fix metadata for remaining files.
    if int(nc_file.name.split(".")[1].split("-")[0]) <= 2005:
        print(nc_file.name)
        subprocess.run(opt_historical + nc_file.name, shell=True)
        relocate(nc_file)
    if int(nc_file.name.split(".")[1].split("-")[0]) >= 2006:
        print(nc_file.name)
        subprocess.run(opt_experimental + nc_file.name, shell=True)
        relocate(nc_file)
    