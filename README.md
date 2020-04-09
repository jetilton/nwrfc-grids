# nwrfc-grids

Utility to download, warp, and convert Northwest River Forecasting netcdf files to Albers Equal Conic dss files.

## Description

An in-depth paragraph about your project and overview of use.

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
>>> g.clip_to_dss("kootenai")
```

### Dependencies

located in `requirements.txt`

