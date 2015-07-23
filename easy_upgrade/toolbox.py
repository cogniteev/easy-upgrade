
from contextlib import contextmanager
import os
import shutil
import tempfile


@contextmanager
def pushd(path):
    cur_dir = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(cur_dir)


@contextmanager
def temp_dir(cleanup=True, **kwargs):
    temp_dir = tempfile.mkdtemp(**kwargs)
    try:
        yield temp_dir
    finally:
        if cleanup:
            shutil.rmtree(temp_dir)
