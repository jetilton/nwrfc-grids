# nwrfc-grids

Utility to download, warp, and convert Northwest River Forecasting netcdf files to Albers Equal Conic dss files.

## Description

so empty

## Getting Started

```
$ git clone git@extranet.crohms.org:rwcds-group/nwrfc-grids.git
$ cd nwrfc-grids
$ conda env create -f environment.yml --prefix ./venv 
$ conda activate ./venv
$ python
>>> from Grids.Grids import Grids
>>> g = Grids()
>>> g.get_grid("QPE", set_dataset=True)
>>> g.dataset
>>> g.warp()
>>> g.clip_to_dss(project="kootenai", cwms_dir="path/to/cwms")
>>> # now go and check the data directory for your dss file
```



