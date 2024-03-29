# cordex-drs-compliance

This repo stores scripts built in Python 3 and BASH to manipulate NetCDF climate data files to prepare them for storarge following the CORDEX data reference syntax, as specified [here](http://is-enes-data.github.io/cordex_archive_specifications.pdf).

In its current state these scripts are built for a specific case of files retrieved by the Climate Futures group at UTAS from CSIRO that needed some manipulations. As a result, they will not work with other filesystems. However, if this program is successful it may be updated in future to be a general use script that extracts data from a NetCDF file that is CORDEX compliant and correctly files it in a specified directory.

## Requirements

This script makes calls to shell through bash, primarily to call upon the netCDF operators (NCO), which is built for linux. As such, this script is best suited towards linux systems.

### Linux Packages
- Python 3.6 or above
- [cdo](https://packages.debian.org/sid/cdo)
- [nco](https://nco.sourceforge.net/nco.html)
