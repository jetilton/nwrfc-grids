# nwrfc-grids

Utility to download, warp, and convert Northwest River Forecasting netcdf files to Albers Equal Conic dss files.

## Description

The [Northwest River Forecast Center (NWRFC)](https://www.nwrfc.noaa.gov/rfc/) offers multiple [data downloads](https://www.nwrfc.noaa.gov/misc/downloads/). 
This utility (nwrfc-grids) pulls NWRFC gridded [climate forcings](https://www.climate.gov/maps-data/primer/climate-forcing) in the [NetCDF](https://en.wikipedia.org/wiki/NetCDF)
file format that cover the Columbia River Basin.  NWRFC offers 4 climate forcings which are:

- Quantitative Precipitation Estimate (QPE)
- Quantitative Temperature Estimate (QTE)
- Quantitative Precipitation Forecast (QPF)
- Quantitative Temperature Forecast (QTF)

Each forcing is a 3-dimensional array (time, x, y) where time is in minutes since 1970-01-01 00:00:00.0 +0000 or UTC upon conversion to datetime and x/y are coordinates according to WGS 1984.  The time dimension are 6-hour time steps and are of shape 4 for a day from what I have seen, but I am told it can be as high as 28 for a week's worth of data in a single file.  Each timestamp is the ending time period for that measurement (reference: spoke with NWRFC staff member Geoffrey Walters).


To understand the data format a recommended video is: https://www.youtube.com/watch?v=XqoetylQAIY&feature=emb_rel_pause
To be able to view netCDF data a utility seen in the video is [Panoply](https://www.giss.nasa.gov/tools/panoply/); a netCDF, HDF and GRIB Data Viewer provided by NASA.

### Sequence

1. Download netCDF file
2. Warp gridded data
3. Clip grids to basins
4. Output data to [esri ascii](http://resources.esri.com/help/9.3/arcgisengine/java/GP_ToolRef/spatial_analyst_tools/esri_ascii_raster_format.htm) file format
5. Convert ascii to .dss


#### Download netCDF file

The data is grabbed using the python library [wget](https://bitbucket.org/techtonik/python-wget/src/default/) and archived in the raw directory.

#### Warp gridded data

The data is warped from [WSG 1984](https://spatialreference.org/ref/epsg/4326/) to [Albers Conical Equal Area](https://spatialreference.org/ref/sr-org/6630/) using the [gdal package](https://gdal.org/) and the [`gdal.warp method`](https://gdal.org/python/osgeo.gdal-module.html#Warp)

#### Clip grids to basins

After the data is warped it clips the larger Columbia River Basin data into smaller basins defined by the config.py file.  It takes a project name and an x/y min/max in Albers Conical Equal Area.

#### Output data to esri ascii

This is an intermediate step required by the CWMS utility asc2dssGrid.exe, which is able to convert the fileformat into dss.

#### Convert ascii to .dss

The asc2dssGrid.exe is the utility to convert data from ascii to dss.  It requires a pathname and the data.  Reading the CWMS documentation **GageInterp**: A Program for Creating a Sequence of HEC-DSS Grids from Time-Series Measurements I found that there were general and specific requirements for how the pathname should be for each data type (precipitation/temperature)

Grid records in DSS are named according to a naming convention that differs slightly from the convention for time-series or paired-data records. Grids represent data over a region instead of at a single location and one grid record contains data for a single time interval or instantaneous value. The naming convention assigns the six pathname parts as follows.

- A-part: Refers to the grid reference system. At present, GageInterp supports only the HRAP and SHG grid systems (see appendices D and E). Other grid systems will be necessary for work outside the conterminous United States.
- B-part: Contains the name of the region covered by the grid. For radar grids, this could be the name of the NWS River Forecast Center that produces the grid. For interpolated grids, this could be the name of a watershed.
- C-part: Refers to the parameter represented by the grid. Examples include PRECIP for precipitation, AIRTEMP for air temperature, SWE for snow-water equivalent, and ELEVATION for ground surface elevation.
- D-part: Contains the start time. This is the starting time of the interval covered by the grid. The date and time are given military-style (DDMMMYYYY for date and HHMM for time on a twenty-four hour clock) and the date and time are separated by a colon (:). All times for grids should be given as UTC. Midnight is represented by 0000 if it is a starting time and 2400 if it is an ending time.
- E-part: Contains the end time. This is the ending time of the interval covered by the grid. The E part is blank for grids of instantaneous values.
- F-part: Refers to the version of the data. The version identifies the source of the data or otherwise distinguishes one set of grids from another. Version labels include STAGEIII for NWS stage III radar products, and INTERPOLATED for grids produced by GageInterp.


Because each grid record represents a single instant or interval of time, the D and E parts of grid pathnames follow a different convention than the one for time series pathnames. For period cumulative (PER-CUM) grids, the D part contains the start date and time of the period and the E part contains the end date and time. For instantaneous (INST-VAL) grids, the D part contains the date and time of the grid values and the E part is blank. Dates and times are given in military style with date separated from time of day by a colon. Grid times should always be given in Universal Coordinated Time (UTC). For example, an instantaneous grid with a D part of 04JUL2001:1500 represents values at 3:00pm UTC (8:00am Pacific Daylight Time) on July 4, 2001

##### Precipitation

Precipitation is in cumulative and labeled period cumulative (PER-CUM).

##### Temperature
Table 3.2 states to use INST-VAL for temperature grids, although this is not true.  The data is an average over the 6-hour time period (reference: spoke with NWRFC staff member Geoffrey Walters).  
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



