import os
from typing import Union

from napari_hierarchical.model import Group

PathLike = Union[str, os.PathLike]


def write_netcdf4(path: PathLike, group: Group) -> None:
    # TODO netCDF4 writer
    raise NotImplementedError()
