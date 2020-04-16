# standard packages
import logging
import sys
import os
import shutil
from datetime import datetime
from datetime import timedelta
import gzip
import subprocess
import glob

# requirements
import pandas as pd
import xarray as xr
from pytz import timezone
import pytz
import numpy as np
import wget
import gdal

# local
from Grids.config import config
from Grids.utils import log_decorator

LOGGER = logging.getLogger(__name__)
LD = log_decorator(LOGGER)
FORMAT = "%(levelname)s - %(asctime)s - %(name)s - %(message)s"


class Grids:
    """Utility class to scrape and process gridded data from 
        the Northwest River Forecast Center (NWRFC).
        url: https://www.nwrfc.noaa.gov/rfc/

    Parameters
    ----------
    pathname : str
        Optional parameter if want to open a local grid. (the default is None).
    data_layer : str
        The data type from the RFC.
        Example: QPE (Quantitative Precipitation Estimate)
        If none is provided it will try to be found in the grid pathname
        Example pathname:QPE.2019020212.nc.
        (the default is None).
    config : dict
        Configuration file for projects with their bounds (xmin,ymin,xmax,ymax)
        used for clipping

    Examples
    -------
    >>> import Grids from main
    >>> g = Grids()
    

    Attributes
    ----------
    dataset : xarray.core.dataset.Dataset
        Opened netcdf file as xarray dataset
    config

    """

    def __init__(self, config=config, verbose=True):
        if verbose:
            logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)
        else:
            logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=FORMAT)
        self.config = config
        self.dataset = None
        self.pathname = None

    @LD
    def set_dataset(self, pathname, year, month, data_layer=None, unzipped_dir=None):
        """Open netcdf file and set it as Grids dataset.

        Parameters
        ----------
        pathname : str
            Path to netcdf file.
        data_layer : str
            The data type from the RFC.
            Example: QPE (Quantitative Precipitation Estimate)
            If none is provided it will try to be found in the grid pathname
            Example pathname:QPE.2019020212.nc.
            (the default is None).
        unzipped_dir : str
            Location to keep a temporary unzipped file if pathname ends in .gz.
        """
        if self.dataset:
            self.dataset.close()
        if pathname[-2:] == "gz":
            if not unzipped_dir:
                unzipped_dir = "temp"
            pathname = self.unzip(pathname, unzipped_dir=unzipped_dir)
        if not data_layer:
            data_layer = pathname.split(".")[0][-3:]
        self.data_layer = data_layer
        self.pathname = pathname
        self.dataset = xr.open_dataset(pathname)
        self._FillValue = self.dataset[self.data_layer].encoding["_FillValue"]
        self.year = year
        self.month = month

    @LD
    def get_grid(
        self,
        data_type,
        date=None,
        directory="raw",
        set_dataset=True,
        unzipped_dir=None,
        force=False,
    ):
        """Get a NWRFC grid.

        Parameters
        ----------
        data_type : str
            The data type from the RFC.
            Example: QPE (Quantitative Precipitation Estimate)
        date : str
            Date in "%Y%m%d" format.  Today is used if `date=None`.
        directory : str
            Directory to store data (the default is "raw").
        set_dataset : boolean
            Open file and set as xarray dataset (the default is True).
        unzipped_dir : str
            Directory to unzip if `set_dataset=True`.  `"temp"` is used
            if not provided.
        force : boolean
            Download data even if found locally.

    
        Examples
        -------
        Examples should be written in doctest format, and
        should illustrate how to use the function/class.
        >>> g = Grids()
        >>> g.get_grid("QPE")
        >>> g.dataset
        """

        if not date:
            date = datetime.now().strftime("%Y%m%d")
        year = date[:4]
        month = date[4:6]

        fname = f"{data_type}.{date}12.nc.gz"
        if os.path.exists(f"{directory}/{fname}") and not force:
            LOGGER.info(f"{directory}/{fname} found locally.")
        else:
            url = f"https://www.nwrfc.noaa.gov/weather/netcdf/{year}/{date}/{fname}"
            LOGGER.info(f"No local copy, attempting to get data {url}")
            try:
                raw_data = wget.download(url)
            except Exception as e:
                LOGGER.error(f"Fatal error in wget for {url}")
                raise e
            LOGGER.info(f"Success, retrieved {raw_data} moving to {directory}")
            try:
                shutil.move(raw_data, os.path.join(directory, raw_data))
            except Exception as e:
                LOGGER.error(f"Could not move file {raw_data}")
                raise e
        if set_dataset:
            self.set_dataset(
                f"{directory}/{fname}",
                year=year,
                month=month,
                unzipped_dir=unzipped_dir,
            )

    @staticmethod
    @LD
    def unzip(pathname, unzipped_dir="temp", remove_old=True):
        """Utility function to unzip files.
        """
        if remove_old:
            for f in glob.glob("temp/*.nc"):
                os.remove(f)
        f = gzip.GzipFile(f"{pathname}", "rb")
        s = f.read()
        f.close()
        fname = pathname.split("/")[-1][:-3]
        outpath = os.path.join(unzipped_dir, fname)
        output = open(f"{outpath}", "wb")
        output.write(s)
        output.close()
        return outpath

    @LD
    def warp(
        self,
        destNameOrDestDS=None,
        dstSRS=None,
        cellsize=2000,
        targetAlignedPixels=True,
    ):
        """Warps data to specified Spatial Reference System (SRS) 
            using gdal library.
            https://spatialreference.org
            https://gdal.org/python/
        Parameters
        ----------
        destNameOrDestDS : str
            Destination output file path.  Will put file in `temp` if
            `destNameOrDestDS=None`
        dstSRS : str
            Spatial Reference system to warp the data to.  
            Albers North American is used if None given.
            Although the gdalwarp can supposedly take the ESPG or SR-org numbers
            I had the most success using proj4js string format.
        cellsize : int
            Output cellsize (the default is 2000).
        targetAlignedPixels : boolean
            whether to force output bounds to be multiple 
            of output resolution (the default is True).

        Examples
        -------
        >>> g = Grids()
        >>> g.get_grid("QPE")
        >>> g.warp()

        """
        srs = self.dataset[self.data_layer].grid_mapping
        srcSRS = self.dataset[srs].attrs["proj4_params"]
        if not dstSRS:
            dstSRS = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 datum=NAD83 +towgs84=1,1,-1,0,0,0,0 +units=m"
        self.cellsize = cellsize
        srcNodata = self._FillValue
        srcDSOrSrcDSTab = gdal.Open(f'NETCDF:"{self.pathname}":{self.data_layer}')
        if not destNameOrDestDS:
            destNameOrDestDS = os.path.join("temp", f"{self.data_layer}.temp.nc")

        LOGGER.info(f"Attempting to warp {self.pathname}")
        try:
            warped = gdal.Warp(
                destNameOrDestDS=destNameOrDestDS,
                srcDSOrSrcDSTab=srcDSOrSrcDSTab,
                srcSRS=srcSRS,
                dstSRS=dstSRS,
                dstNodata=float(srcNodata),
                format="NETCDF",
                xRes=cellsize,
                yRes=cellsize,
                targetAlignedPixels=targetAlignedPixels,
            )
            LOGGER.info(f"Success, warped {self.pathname}")
        except Exception as e:
            LOGGER.error(f"Fatal error in warp gdal.Warp")
            raise e
        warped = None

        # gdal.warp Creation Issues
        # reference: https://gdal.org/drivers/raster/netcdf.html
        # This driver supports creation of NetCDF file following the CF-1 convention.
        # You may create set of 2D datasets. Each variable array is named Band1, Band2, … BandN.
        # Each band will have metadata tied to it giving a short description of the data it contains.

        # This means that gdal.warp will create a new .nc file with the data layer split bc it
        # cannot maintain the 3d architecture (x,y,time) only can do 2d (x,y)
        # so I am concatenating the new file here and setting it to my dataset to maintain the
        # original architecture
        warped = xr.open_dataset(destNameOrDestDS)
        time = self.dataset["time"]
        bands = [warped[f"Band{b}"] for b in range(1, len(time) + 1)]
        warped[self.data_layer] = xr.concat(bands, time)
        self.dataset.close()
        self.dataset = warped.drop_vars([f"Band{b}" for b in range(1, len(time) + 1)])
        warped.close()

    @staticmethod
    @LD
    def _to_esri_ascii(grid, output, xllcorner, yllcorner, cellsize, _FillValue):
        """utility function to get grid into esri ascii format.
        http://resources.esri.com/help/9.3/arcgisengine/java/GP_ToolRef/spatial_analyst_tools/esri_ascii_raster_format.htm
        http://gis.humboldt.edu/OLM/Courses/GSP_318/02_X_5_WritingGridASCII.html
        """

        nrows, ncols = grid.shape
        f = open(f"{output}", "w")
        f.write(f"ncols         {ncols}\n")
        f.write(f"nrows         {nrows}\n")
        f.write(f"xllcorner     {xllcorner}\n")
        f.write(f"yllcorner     {yllcorner}\n")
        f.write(f"cellsize      {cellsize}\n")
        f.write(f"NODATA_value  {_FillValue:.5f}\n")
        np.savetxt(f, grid, fmt="%.5f", delimiter=" ")
        f.close()

    @staticmethod
    @LD
    def clip(xmin, ymin, xmax, ymax, x, y, grid):
        """Utility function to clip a 3 dimmensional grid given specified y/x min/max.
            Assumes data in dimensions [time,y,x]
        """
        x_min_idx = np.argmin(x < xmin)
        y_min_idx = np.argmin(y < ymin)

        x_max_idx = np.argmax(x > xmax)
        y_max_idx = np.argmax(y > ymax)

        xllcorner = x[x_min_idx]
        yllcorner = y[y_min_idx]
        return (
            grid[:, y_min_idx : y_max_idx + 1, x_min_idx : x_max_idx + 1],
            xllcorner,
            yllcorner,
        )

    @staticmethod
    @LD
    def get_times(time, dtype, timestep=6):
        """Utility function to format times for dss file entry
        DSS is very strange about how it accepts the times for both precip and temp
        The below is ugly bc I had to make several changes, could probably be 
        redone so it isn't such a mess.
        """
        time = pd.to_datetime(str(time))
        if time.hour == 0:
            end_time = time - timedelta(hours=24)
            end_time = (
                (time - timedelta(hours=24))
                .strftime("%d%b%Y:%H%M")
                .replace("0000", "2400")
            )
        else:
            end_time = time.strftime("%d%b%Y:%H%M")
        if dtype == "INST-VAL":
            end_time = ""
        start_time = time - timedelta(hours=timestep)
        if dtype == "INST-VAL" and start_time.hour == 0:
            start_time = (
                (start_time - timedelta(hours=24))
                .strftime("%d%b%Y:%H%M")
                .replace(":0000", ":2400")
            )
        else:
            start_time = start_time.strftime("%d%b%Y:%H%M")
        LOGGER.info(f"{time} converted to {start_time}, {end_time}.")
        return start_time, end_time

    @LD
    def clip_to_dss(self, project, dss_pathname=None):
        """Clip dataset and store in dss file given 
            a project name located in config.

        Parameters
        ----------
        project : str
            Project name located in `self.config`.

        Examples
        -------
        >>> g = Grids(config = config)
        >>> g.get_grid("QPE")
        >>> g.warp()
        >>> g.clip_to_dss("kootenai")

        """
        try:
            proj_conf = self.config[project]
        except TypeError as e:
            LOGGER.warning("Configuration is not set")
            raise e
        except KeyError as e:
            LOGGER.warning("Project does not exist in configuration")
            raise e

        grid = self.dataset[self.data_layer].values
        x = self.dataset["x"].values
        y = self.dataset["y"].values

        clipped, xllcorner, yllcorner = self.clip(x=x, y=y, grid=grid, **proj_conf)

        # Gathering parts for the dss pathname
        units = self.dataset[self.data_layer].units
        data_dict = {"P": "PRECIP", "T": "TEMPERATURE"}
        data_type = data_dict[self.data_layer[1]]

        # gathering parts to run asc2dssGrid
        # see Corps Water Management System (CWMS) Documentation: GageInterp
        # GageInterp: A Program for Creating a Sequence of HEC-DSS Grids
        # from Time-Series Measurements
        if data_type == "PRECIP":
            dtype = "PER-CUM"
        elif data_type == "TEMPERATURE":
            dtype = "INST-VAL"
            units = '"DEG F"'

        for idx, time in enumerate(self.dataset["time"].values):
            start_time, end_time = self.get_times(time, dtype=dtype)

            dss_path = f"/SHG/{project}/{data_type}/{start_time}/{end_time}/RFC-{self.data_layer}/"
            grid = clipped[idx]

            asc_pathname = os.path.join("temp", f"{self.data_layer}_temp.asc")
            if not dss_pathname:
                dss_pathname = os.path.join(
                    "data", f"NWD_{self.data_layer}.{self.year}.{self.month}.dss"
                )
            self._to_esri_ascii(
                grid, asc_pathname, xllcorner, yllcorner, self.cellsize, self._FillValue
            )

            # asc2dssGrid = os.path.join(cwms_dir, "common", "grid", "asc2dssGrid")
            cmd = f"asc2dssGrid in={asc_pathname} dss={dss_pathname} path={dss_path} grid=SHG dunits={units} dtype={dtype}"
            LOGGER.info(f"Attempting to run: {cmd}")
            try:
                subprocess.run(cmd)
            except Exception as e:
                LOGGER.error(f"Fatal error in {cmd}", exc_info=True)
                raise e

    @staticmethod
    @LD
    def get_grids(data_types, start, end=None, directory="raw", force=False):
        """Utility function to download multiple grids at once
        """
        fmt = "%Y%m%d"
        if data_types == "all":
            data_types = ["QPE", "QTF", "QTE", "QPF"]
        if not end:
            end = datetime.now()
        else:
            end = datetime.strptime(end, fmt)
        start = datetime.strptime(start, fmt)
        delta = end - start
        for data_type in data_types:
            for i in range(delta.days + 1):
                date = (start + timedelta(days=i)).strftime(fmt)
                try:
                    get_grid(
                        data_type=data_type,
                        date=date,
                        directory=directory,
                        force=force,
                        set_dataset=False,
                    )
                except:
                    LOGGER.error(f"Fatal error in wget for {date}", exc_info=True)
                    continue
