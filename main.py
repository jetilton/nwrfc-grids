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
from config import config
from utils import log_decorator

LOGGER = logging.getLogger(__name__)
LD = log_decorator(LOGGER)
FORMAT = "%(levelname)s - %(asctime)s - %(name)s - %(message)s"
logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=FORMAT)


class Grids:
    def __init__(self, pathname=None, data_layer=None, config=None):
        if pathname:
            self.set_dataset(pathname, data_layer=None)
        else:
            self.dataset = None
        self.config = config

    @LD
    def set_dataset(self, pathname, data_layer=None, unzipped_dir=None):
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

        if not date:
            date = datetime.now().strftime("%Y%m%d")
        year = date[:4]
        fname = f"{data_type}.{date}12.nc.gz"
        if os.path.exists(f"{directory}/{fname}") and not force:
            LOGGER.info(f"{directory}/{fname} found locally.")
        else:
            url = f"https://www.nwrfc.noaa.gov/weather/netcdf/{year}/{date}/{fname}"
            LOGGER.info(f"Attempting to get data {url}")
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
            self.set_dataset(f"{directory}/{fname}", unzipped_dir=unzipped_dir)

    @staticmethod
    @LD
    def unzip(pathname, unzipped_dir="temp", remove_old=True):
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

        ncols, nrows = grid.shape
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

    @LD
    @staticmethod
    def get_times(time, timestep=6):
        end_time = (
            pd.to_datetime(str(time)).strftime("%d%b%Y:%H%M").replace("0000", "2400")
        )
        start_time = (pd.to_datetime(str(time)) - timedelta(hours=timestep)).strftime(
            "%d%b%Y:%H%M"
        )
        return start_time, end_time

    @LD
    @staticmethod
    def asc_to_dss(asc_pathname, dss_pathname, dss_path):
        gridconvert_string = (
            os.path.join(os.getcwd(), "asc2DssGrid.sh")
            + " zlib=true GRID=SHG in="
            + asc_pathname
            + " dss="
            + dss_pathname
            + " path="
            + dss_path
        )
        subprocess.call(gridconvert_string, shell=True)

    @LD
    def clip_to_dss(self, project):
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

        for idx, time in enumerate(self.dataset["time"].values):
            start_time, end_time = self.get_times(time)
            dss_path = (
                f"/SHG/{project}/PRECIP/{start_time}/{end_time}/RFC-{self.data_layer}/"
            )
            grid = clipped[idx]

            asc_pathname = os.path.join("temp", f"{self.data_layer}_temp.asc")
            dss_pathname = "path/to/file.dss"
            self._to_esri_ascii(
                grid, asc_pathname, xllcorner, yllcorner, self.cellsize, self._FillValue
            )
            self.asc_to_dss(asc_pathname, dss_pathname, dss_path)

    @LD
    @staticmethod
    def get_grids(data_types, start, end=None, directory="raw", force=False):
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
