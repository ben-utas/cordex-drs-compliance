#!/usr/bin/env python3

import argparse  # Provides functions for parsing command line arguments.
import shutil  # Provides functions for copying files.
import subprocess  # Provides functions for running shell commands.
from pathlib import Path  # Provides functions for manipulating files.

parser = argparse.ArgumentParser(
    prog="CORDEX Compliance Enforcer and Path Builder",
    description="Fix metadata and rename files to comply with CORDEX DRS standard."
)

parser.add_argument(
    '-t', '--target',
    help='.',
    type=Path,
    default=Path('.')
)

parser.add_argument(
    '-d', '--destination',
    help='Destination directory for output files.',
    type=Path,
    default=Path('.')
)

parser.add_argument(
    '-m', '--gcm_model',
    help='Model used for experiment.',
    type=str,
    choices=[
        'CNRM-CERFACS-CNRM-CM5', 'CSIRO-BOM-ACCESS1-0', 'MIROC-MIROC5',
        'MOHC-HadGEM2-CC', 'NCC-NorESM1-M', 'NOAA-GFDL-GFDL-ESM2M'
    ]
)

destination = Path(parser.parse_args().destination)

if not destination.exists() and not destination.is_dir():
    print("Destination directory does not exist.")
    exit()

invariant_variables = [
    "grid", "he", "orog", "sftlf", "sigmu", "vegt", "areacella", "sftgif",
    "mrsofc", "rootd"
]

# Search for all files with a .nc extension in the current and sub directories.
path = Path(parser.parse_args().target)
nc_files = list(path.glob('**/*.nc'))

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
        "ncdump -h " + str(nc_file),
        stdout=subprocess.PIPE,
        shell=True
    )
    nc_headers = nc_headers.stdout.decode("utf-8").split('\n')

    allocated = {}
    showname = subprocess.run(
        "cdo -s showname " + str(nc_file), stdout=subprocess.PIPE, shell=True
    )

    allocated["variable_name"] = \
        showname.stdout.decode("utf-8") \
        .split('\n')[0].strip()

    if allocated["variable_name"] not in invariant_variables:
        showdate = subprocess.run(
            "cdo -s showdate " + str(nc_file),
            stdout=subprocess.PIPE,
            shell=True
        )
        dates = showdate.stdout.decode("utf-8").split("  ")
        dates = [d for d in dates if d]
        allocated["start_date"] = dates[0].replace('-', '').strip()
        allocated["end_date"] = dates[-1].replace('-', '').strip()
    allocated["product"] = "output"
    allocated["project_id"] = "CORDEX"
    # Dictionary with variable names yet to be allocated.
    unallocated = dict.fromkeys([
        "domain", "driving_model_id", "driving_experiment_name",
        "driving_model_ensemble_member", "model_id", "rcm_version_id",
        "frequency", "institute_id"
    ])
    for_fix = dict.fromkeys([
        "source", "date_header"
    ])

    # Find the string in nc_headers that contains each variable.
    for s in nc_headers:
        key = ""
        for k in unallocated:
            if k in s:
                key = k
                break
        for k in for_fix:
            if k in s:
                for_fix[k] = s.split("\"")[1]
        if key == "":
            continue
        unallocated.pop(key)
        allocated[key] = s.split("\"")[1]

    # Make sure all keys have been allocated.
    if len(unallocated) != 0:
        print("Not all CORDEX variables are present for " + nc_file.name)
        fix_global_variables(nc_file, for_fix)
        return

    # Build the new file name and path.
    cordex_path = destination / allocated["project_id"] / \
        allocated["domain"] / allocated["institute_id"] / \
        allocated["driving_model_id"] / allocated["driving_experiment_name"] / \
        allocated["driving_model_ensemble_member"] / allocated["model_id"] / \
        allocated["rcm_version_id"] / allocated["frequency"] / \
        allocated["variable_name"]

    cordex_name = "_".join([
        allocated["variable_name"], allocated["domain"],
        allocated["driving_model_id"], allocated["driving_experiment_name"],
        allocated["driving_model_ensemble_member"], allocated["model_id"],
        allocated["rcm_version_id"], allocated["frequency"]
    ])

    if allocated["variable_name"] not in invariant_variables:
        cordex_name = \
            cordex_name + "_" \
            + "-".join([allocated["start_date"], allocated["end_date"]])

    cordex_name = cordex_name + ".nc"

    new_home = Path.joinpath(cordex_path, cordex_name)
    if not Path.exists(cordex_path):
        Path.mkdir(cordex_path, parents=True)
    shutil.copy(nc_file, new_home)


def fix_global_variables(nc_file: Path, for_fix: dict):
    nc_fix_hist = nc_file.name + "_fixedhist.nc"
    nc_fix_exp = nc_file.name + "_fixedexp.nc"

    gcm_model = str(parser.parse_args().gcm_model)

    subprocess.run(
        "ncatted -O -h -a ,global,d,, " +
        str(nc_file) + " " + str(path) + "/" + nc_fix_hist, shell=True
    )

    nc_fix_hist = list(path.glob(nc_fix_hist))[0]
    shutil.copy(nc_fix_hist, str(path) + "/" + nc_fix_exp)
    nc_fix_exp = list(path.glob(nc_fix_exp))[0]

    showname = subprocess.run(
        "cdo -s showname " + str(nc_file), stdout=subprocess.PIPE, shell=True
    )

    variable_name = showname.stdout.decode("utf-8").split('\n')[0].strip()

    if variable_name in invariant_variables:
        freq = "fx"
    else:
        freq = "day"
        showdate = subprocess.run(
            "cdo -s showdate " + str(nc_file),
            stdout=subprocess.PIPE,
            shell=True
        )
        dates = showdate.stdout.decode("utf-8").split("  ")
        dates = [d for d in dates if d]
        start_date = dates[0].replace('-', '').strip()
        end_date = dates[-1].replace('-', '').strip()

    source = for_fix["source"]
    try:
        d = for_fix["creation_date"]
    except:
        d = "20170101"

    creation_date = '-'.join([d[:4], d[4:6], d[6:]]) + "T00:00:00UTC"

    experiment_id = "historical"

    opt_fix = (
        "ncatted -O -h " +
        "-a institute_id,global,o,c,CSIRO " +
        "-a institution,global,o,c,'CSIRO Australia' " +
        "-a model_id,global,o,c,CSIRO-CCAM-r3355 " +
        "-a rcm_version_id,global,o,c,v1 " +
        "-a experiment_id,global,o,c," + experiment_id + " " +
        "-a experiment,global,o,c,'Climate change run using " + gcm_model + " " + experiment_id + " r1i1p1' " +
        "-a driving_model_id,global,o,c," + gcm_model + " " +
        "-a driving_model_ensemble_member,global,o,c,r1i1p1 " +
        "-a driving_experiment,global,o,c,'" + gcm_model + "; " + experiment_id + "; r1i1p1' " +
        "-a driving_experiment_name,global,o,c, " + experiment_id + " " +
        "-a domain,global,o,c,GLB-50i " +
        "-a comment,global,o,c,GLB-50i " +
        "-a frequency,global,o,c," + freq + " " +
        "-a product,global,o,c,output " +
        "-a project_id,global,o,c,CORDEX " +
        "-a contact,global,o,c,ccam@csiro.au " +
        "-a references,global,o,c,https://confluence.csiro.au/display/CCAM " +
        "-a il,global,o,c,192 " +
        "-a kl,global,o,c,35 " +
        "-a schmidt,global,o,c,1. " +
        "-a rlon,global,o,c,0. " +
        "-a rlat,global,o,c,0. " +
        "-a creation_date,global,o,c," + creation_date + " " +
        "-a source,global,o,c," + source
    )

    subprocess.run(opt_fix + str(nc_fix_hist), shell=True)

    experiment_id = "rcp85"

    opt_fix = (
        "ncatted -O -h " +
        "-a institute_id,global,o,c,CSIRO " +
        "-a institution,global,o,c,'CSIRO Australia' " +
        "-a model_id,global,o,c,CSIRO-CCAM-r3355 " +
        "-a rcm_version_id,global,o,c,v1 " +
        "-a experiment_id,global,o,c," + experiment_id + " " +
        "-a experiment,global,o,c,'Climate change run using " + gcm_model +
        " " + experiment_id + " r1i1p1' " +
        "-a driving_model_id,global,o,c," + gcm_model + " " +
        "-a driving_model_ensemble_member,global,o,c,r1i1p1 " +
        "-a driving_experiment,global,o,c,'" + gcm_model + "; " +
        experiment_id + "; r1i1p1' " +
        "-a driving_experiment_name,global,o,c, " + experiment_id + " " +
        "-a domain,global,o,c,GLB-50i " +
        "-a comment,global,o,c,GLB-50i " +
        "-a frequency,global,o,c," + freq + " " +
        "-a product,global,o,c,output " +
        "-a project_id,global,o,c,CORDEX " +
        "-a contact,global,o,c,ccam@csiro.au " +
        "-a references,global,o,c,https://confluence.csiro.au/display/CCAM " +
        "-a il,global,o,c,192 " +
        "-a kl,global,o,c,35 " +
        "-a schmidt,global,o,c,1. " +
        "-a rlon,global,o,c,0. " +
        "-a rlat,global,o,c,0. " +
        "-a creation_date,global,o,c," + creation_date + " " +
        "-a source,global,o,c," + source
    )

    subprocess.run(opt_fix + str(nc_fix_exp), shell=True)

    move_fixes(gcm_model, experiment_id, variable_name,
               freq, start_date, end_date, nc_fix_hist)
    experiment_id = "historical"
    move_fixes(gcm_model, experiment_id, variable_name,
               freq, start_date, end_date, nc_fix_exp)

    nc_fix_hist.unlink()
    nc_fix_exp.unlink()

    return


def move_fixes(gcm_model, experiment_id, variable_name, freq, start_date, end_date, nc_fix):
    # Build the new file name and path.
    cordex_path = destination / "CORDEX" / "GLB-50i" / "CSIRO" / \
        gcm_model / experiment_id / "r1i1p1" / \
        "CSIRO-CCAM-r3355" / "v1" / "fx" / variable_name

    cordex_name = "_".join([
        variable_name, "GLB-50i", gcm_model, experiment_id,
        "r1i1p1", "CSIRO-CCAM-r3355", "v1", freq
    ])

    if variable_name not in invariant_variables:
        cordex_name = \
            cordex_name + "_" \
            + "-".join([start_date, end_date])

    cordex_name = cordex_name + ".nc"

    new_home = Path.joinpath(cordex_path, cordex_name)
    if not Path.exists(cordex_path):
        Path.mkdir(cordex_path, parents=True)
    shutil.copy(nc_fix, new_home)


historical_dates = ["1950", "1960", "1970", "1980", "1990", "2000-2005"]
experimental_dates = [
    "2006-2009", "2010", "2020", "2030", "2040", "2050", "2060", "2070",
    "2080", "2090"
]

for nc_file in nc_files:
    # Find files with name containing the date range 2000-2009, and split this file into a historical and projected file with historical file having metadata updated.
    print(nc_file.name)
    if "2000-2009" in nc_file.name:
        nc_historical = nc_file.name.split(".")[0] + ".2000-2005.nc"
        nc_experiment = nc_file.name.split(".")[0] + ".2006-2009.nc"
        subprocess.run(
            "cdo -s selyear,2000/2005 "
            + str(nc_file) + " " + str(path) + "/" + nc_historical, shell=True
        )
        subprocess.run(
            "cdo -s selyear,2006/2009 "
            + str(nc_file) + " " + str(path) + "/" + nc_experiment, shell=True
        )
        try:
            nc_historical = list(path.glob(nc_historical))[0]
            nc_experiment = list(path.glob(nc_experiment))[0]
        except:
            print(nc_file.name +
                  " failed to split into experimental and historical files.")
        else:
            subprocess.run(opt_historical + str(nc_historical), shell=True)
            subprocess.run(opt_experimental + str(nc_experiment), shell=True)
            relocate(nc_historical)
            relocate(nc_experiment)
            nc_historical.unlink()
            nc_experiment.unlink()
    # Fix metadata for remaining files.
    elif any(date in nc_file.name for date in historical_dates):
        subprocess.run(opt_historical + str(nc_file), shell=True)
        relocate(nc_file)
    elif any(date in nc_file.name for date in experimental_dates):
        subprocess.run(opt_experimental + str(nc_file), shell=True)
        relocate(nc_file)
    else:
        relocate(nc_file)
