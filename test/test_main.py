import os
import glob
import sys
import shutil
from datetime import datetime

import pytest
import pandas as pd
import json

from Grids.Grids import Grids


@pytest.fixture()
def g():
    print("make resource")
    g = Grids()
    yield g
    g.dataset.close()
    for f in glob.glob("temp/*.nc"):
        os.remove(f)


class TestClass(object):
    def test_get_grid_date_doesnt_exist_no_date(self, g, caplog):
        # I want to delete todays data if it exists to run the test
        data_type = "QPE"
        date = datetime.now().strftime("%Y%m%d")
        fname = f"{data_type}.{date}12.nc.gz"
        if os.path.exists(os.path.join("raw", fname)):
            os.remove(os.path.join("raw", fname))

        # this is the actual test
        g.get_grid(data_type)
        assert g.dataset
        assert "No local copy" in caplog.text

    def test_get_grid_date_already_exists(self, g, caplog):
        g.get_grid("QPE")
        assert g.dataset
