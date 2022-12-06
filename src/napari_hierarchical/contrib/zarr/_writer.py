import os
from typing import Union

from napari_hierarchical.model import Group

PathLike = Union[str, os.PathLike]


def write_zarr(path: PathLike, group: Group) -> None:
    # TODO Zarr writer
    raise NotImplementedError()
