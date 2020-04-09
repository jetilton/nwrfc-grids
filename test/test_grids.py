import os
import glob
import sys
import shutil
from datetime import datetime
import logging

import pytest
import pandas as pd
import json

from Grids.Grids import Grids


@pytest.fixture()
def g():
    g = Grids()
    yield g
    g.dataset.close()
    for f in glob.glob("temp/*.nc"):
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
            g.get_grid("QPE")
            assert g.dataset
            assert "found locally." in self._caplog.records[0].message

    def test_warp(self, g):
        g.get_grid("QPE")
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

    def test_clip_to_dss_precipitation(self):
        pass

    def test_clip_to_dss_temperature(self):
        pass
