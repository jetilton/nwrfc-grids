# nwrfc-grids

Utility to download, warp, and convert Northwest River Forecasting netcdf files to Albers Equal Conic dss files.

## Description

An in-depth paragraph about your project and overview of use.

## Getting Started

```
$ git clone git@extranet.crohms.org:rwcds-group/nwrfc-grids.git
$ cd nwrfc-grids
$ conda create -y --name grds python==3.7
$ conda install -f -y -q --name grds --file requirements.txt
$ conda activate grds
$ python
>>> from main import Grids
>>> g = Grids()
>>> g.get_grid("QPE", set_dataset=True)
>>> g.dataset
```


### Dependencies

located in `requirements.txt`

