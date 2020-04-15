# nwrfc-grids

Utility to download, warp, and convert Northwest River Forecasting netcdf files to Albers Equal Conic dss files.

## Description

The [Northwest River Forecast Center (NWRFC)](https://www.nwrfc.noaa.gov/rfc/) offers multiple [data downloads](https://www.nwrfc.noaa.gov/misc/downloads/). 

## Getting Started

```
$ git clone git@extranet.crohms.org:rwcds-group/nwrfc-grids.git
$ cd nwrfc-grids
$ conda env create -f environment.yml --prefix ./venv 
$ conda activate ./venv
$ python cli g2dss --projects kootenai --data_types QPE --start 20200401
```
Now go and check the data directory for your dss file

## Other cli examples

```
$ conda activate ./venv
$ python cli g2dss --projects kootenai,deschutes --data_types QPE,QTE --start 20200401 --end 20200404
$ python cli g2dss --projects kootenai
$ python cli g2dss 
```



