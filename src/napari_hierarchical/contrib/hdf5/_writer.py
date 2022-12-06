import os
from typing import Union

from napari_hierarchical.model import Group

PathLike = Union[str, os.PathLike]


def write_hdf5(path: PathLike, group: Group) -> None:
    # TODO HDF5 writer
    raise NotImplementedError()
