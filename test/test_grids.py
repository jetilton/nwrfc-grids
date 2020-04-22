import os
import glob
import sys
import shutil
from datetime import datetime
from datetime import timedelta
import logging

import pytest
import pandas as pd
import json

from Grids.Grids import Grids


@pytest.fixture()
def g():
    g = Grids()
    yield g
    if g.dataset:
        g.dataset.close()
    for f in glob.glob("test/temp/*.nc"):
        os.remove(f)
    for f in glob.glob("test/data/*.nc"):
        os.remove(f)
    for f in glob.glob("temp/*.nc"):
        os.remove(f)
    for f in glob.glob("raw/*.gz"):
        os.remove(f)


class TestClass(object):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        # https://stackoverflow.com/a/50375022/4296857
        self._caplog = caplog

    def test_get_grid_date_doesnt_exist_no_date(self, g):
        # I want to delete todays data if it exists to run the test
        data_type = "QPE"
        date = datetime.now().strftime("%Y%m%d")
        fname = f"{data_type}.{date}12.nc.gz"
        if os.path.exists(os.path.join("raw", fname)):
            os.remove(os.path.join("raw", fname))

        with self._caplog.at_level(logging.INFO):
            g.get_grid("QPE")
            assert g.dataset
            assert (
                "No local copy, attempting to get data"
                in self._caplog.records[0].message
            )

    def test_get_grid_date_already_exists(self, g):

        with self._caplog.at_level(logging.INFO):
            g.get_grid("QPE", "20200421")
            g.get_grid("QPE", "20200421")
            assert g.dataset
            assert "found locally." in self._caplog.records[1].message

    def test_warp(self, g):
        g.get_grid("QPE", "20200421")
        assert g.dataset
        assert "crs" in g.dataset.data_vars
        # I want to get the time shape before the warp
        # this shouldn't change, x and y can
        t_shape = g.dataset["time"].values.shape[0]
        with self._caplog.at_level(logging.INFO):
            g.warp()
            assert "Success, warped" in self._caplog.records[1].message

        assert "albers_conical_equal_area" in g.dataset.data_vars
        assert "crs" not in g.dataset.data_vars
        g_shape = g.dataset["QPE"].values.shape
        x_shape = g.dataset["x"].values.shape[0]
        y_shape = g.dataset["y"].values.shape[0]

        assert g_shape == (t_shape, y_shape, x_shape)

    def test_clip_to_dss(self):
        pass

    def test_split(self, g):
        hrs = [-6, 0, 6, 12]

        g.get_grids("QPE", "20180421", "20180423", force=True)

        for f in glob.glob("raw/*.gz"):
            date = f.split("QPE.")[1].split("12.nc.gz")[0]
            d = datetime.strptime(date, "%Y%m%d")
            expected_dates = pd.to_datetime([d + timedelta(hours=h) for h in hrs])
            g.get_grid("QPE", date)
            times = g.dataset["time"].values
            assert times.shape[0] == 4
            dates = pd.to_datetime(g.dataset["time"].values)
            for a, b in zip(dates, expected_dates):
                assert a == b
