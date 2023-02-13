#!/usr/bin/env python3

import argparse # Provides functions for parsing command line arguments.
import shutil # Provides functions for copying files.
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

target = Path(parser.parse_args().destination)

if not target.exists() and not target.is_dir():
    print("Destination directory does not exist.")
    exit()

invariant_variables = [
    "grid", "he", "orog", "sftlf", "sigmu", "vegt", "areacella", "sftgif", 
    "mrsofc", "rootd"
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
    nc_headers = subprocess.run(
        "ncdump -h " + nc_file.name,
        stdout=subprocess.PIPE,
        shell=True
    )
    nc_headers = nc_headers.stdout.decode("utf-8").split('\n')
    
    allocated = {}
    allocated["variable_name"] = cdo.showname(input=nc_file.name)[0]
    if allocated["variable_name"] not in invariant_variables:
        dates = cdo.showdate(input=nc_file.name)[0].split('  ')
        allocated["start_date"] = dates[0].replace('-', '')
        allocated["end_date"] = dates[-1].replace('-', '')
    allocated["product"] = "output"
    allocated["project_id"] = "CORDEX"
    # Dictionary with variable names yet to be allocated.
    unallocated = dict.fromkeys([
        "domain", "driving_model_id", "driving_experiment_name", 
        "driving_model_ensemble_member", "model_id", "rcm_version_id", 
        "frequency", "institute_id"
    ])
    
    # Find the string in nc_headers that contains each variable.
    for s in nc_headers:
        key = ""
        for k in unallocated:
            if k in s:
                key = k
                break
        if key == "":
            continue
        unallocated.pop(key)
        allocated[key] = s.split("\"")[1]
    
    # Make sure all keys have been allocated.
    if len(unallocated) != 0:
        print("Not all CORDEX variables are present for " + nc_file.name)
        exit()
    
    # Build the new file name and path.
    cordex_path = target / allocated["project_id"] / allocated["domain"] / allocated["institute_id"] / allocated["driving_model_id"] / allocated["driving_experiment_name"] / allocated["driving_model_ensemble_member"] / allocated["model_id"] / allocated["rcm_version_id"] / allocated["frequency"] / allocated["variable_name"] 
    
    cordex_name = "_".join([allocated["variable_name"], allocated["domain"], allocated["driving_model_id"], allocated["driving_experiment_name"], allocated["driving_model_ensemble_member"], allocated["model_id"], allocated["rcm_version_id"], allocated["frequency"]])
    
    if allocated["variable_name"] not in invariant_variables:
        cordex_name = cordex_name + "_" + "-".join([allocated["start_date"], allocated["end_date"]])
    cordex_name = cordex_name + ".nc"
    
    new_home = Path.joinpath(cordex_path, cordex_name)
    if not Path.exists(cordex_path):
        Path.mkdir(cordex_path, parents=True)
    shutil.copy(nc_file, new_home)
    

for nc_file in nc_files:
    # Find files with name containing the date range 2000-2009, and split this file into a historical and projected file with historical file having metadata updated.
    if "2000-2009" in nc_file.name:
        nc_historical = nc_file.name.split(".")[0] + ".2000-2005.nc"
        nc_experiment = nc_file.name.split(".")[0] + ".2006-2009.nc"
        cdo.selyear("2000/2005", input=nc_file.name, output=nc_historical)
        cdo.selyear("2006/2009", input=nc_file.name, output=nc_experiment)
        subprocess.run(opt_historical + nc_historical, shell=True)
        subprocess.run(opt_experimental + nc_experiment, shell=True)
        nc_historical = list(path.glob(nc_historical))[0]
        nc_experiment = list(path.glob(nc_experiment))[0]
        relocate(nc_historical)
        relocate(nc_experiment)
        nc_historical.unlink()
        nc_experiment.unlink()
    # Fix metadata for remaining files.
    elif int(nc_file.name.split(".")[1].split("-")[0]) <= 2005:
        subprocess.run(opt_historical + nc_file.name, shell=True)
        relocate(nc_file)
    elif int(nc_file.name.split(".")[1].split("-")[0]) >= 2006:
        subprocess.run(opt_experimental + nc_file.name, shell=True)
        relocate(nc_file)
    