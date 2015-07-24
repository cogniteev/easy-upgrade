
from contextlib import contextmanager
import os
import os.path as osp
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


def find_executable(*names, **kwargs):
    for name in names:
        if osp.isabs(name):
            return name
        for path in os.environ['PATH'].split(os.pathsep):
            f = osp.join(path, name)
            if osp.isfile(f) and os.access(f, os.X_OK):
                return f
    if kwargs.get('raise_if_missing', True):
        if len(names) > 1:
            raise Exception(
                "Could not find these executables in PATH: " +
                ", ".join(names)
            )
        else:
            raise Exception(
                "Could not find executable {} in PATH".format(*names)
            )
