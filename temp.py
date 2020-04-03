from netCDF4 import Dataset
import pandas as pd
import os
import numpy as np
import datetime
import time
import subprocess
import string
import sys
import itertools
import pytz
    
fr = Dataset("temp/QPE.2020032812.nc")
variable = "QPE"
print(fr)
#ppt = fr.variables[variable][:, :, :]
ta = fr.variables[variable][:, :, :]
lons = fr.variables['x'][:]
lats = fr.variables['y'][:]
time = fr.variables['time'][:]
fr.close()

lon, lat = np.meshgrid(lons, lats)

# Define different projections to use
proj4args_aea = '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 datum=NAD83 +towgs84=1,1,-1,0,0,0,0 +units=m'

#Source Geometry
origin_grid = pyresample.geometry.GridDefinition(lons=lon, lats=lat)

#Target Geometry

name = 'Albers Equal Area'
proj_id = 'aea'
x_size = len(lon_targ)
y_size = len(lat_targ)
proj4_args = proj4args_aea
area_extent = (
min(lon_targ) - target_res * .5, min(lat_targ) - target_res * .5,
max(lon_targ) + target_res * .5, max(lat_targ) + target_res * .5)


for t in range(len(time)-1):
    t += 1

    #now write out the data in asc
    time[t] += timeOffset(datetime.datetime.fromtimestamp(time[t] * 60))
    t_stamp = datetime.datetime.fromtimestamp(time[t] * 60)
    t_stamp = t_stamp.replace(hour=snap(t_stamp.hour,6))

    date = t_stamp.strftime('%Y%m%d%H')
    year = str(t_stamp.year)
    month = str(t_stamp.strftime("%m"))
    hr = t_stamp.hour

    #now convert the asc and store in dss file
    dss_out = '../temp/' + 'NWD_temp.' + year + '.' + month + '.dss'

    # Some manipulation of date strings to get the 24 hour in correct format for DSS
    if hr == 0:
    endtime = (t_stamp - datetime.timedelta(hours=24)).strftime('%d%b%Y:%H%M').replace( '0000', '2400')
    starttime = (t_stamp - datetime.timedelta(hours=6)).strftime('%d%b%Y:%H%M')
    print("starttime=" + starttime + "endtime=" + endtime)
    else:
    endtime = t_stamp.strftime('%d%b%Y:%H%M')
    starttime = (t_stamp - datetime.timedelta(hours=6)).strftime('%d%b%Y:%H%M')

    dss_path = "/SHG/" + project + "/TEMPERATURE/" + endtime + "//RFC-" + variable + "/"
    print(dss_path)



def timeOffset (dt):
  """
    dt is a datetime object
    function will return 480 if in Standard time or 420 if in Daylight Savings time.
  """
  localtime = pytz.timezone('US/Pacific')
  if bool(localtime.localize(dt).dst()):
    print("DST")
    return 420.
  return 480.

def snap (value, interval):
  return int(round (value/float(interval))*interval)