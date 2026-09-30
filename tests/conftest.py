import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import pytest

from backend.database.init_db import init_db, get_connection
from backend.database.seed_reference_data import seed


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("db")
    path = str(tmp / "test_tce.db")
    init_db(path)
    seed(db_path=path)
    return path


@pytest.fixture()
def conn(db_path):
    c = get_connection(db_path)
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
    finally:
        c.close()