import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_hierarchical.hookspecs import GroupReaderFunction, GroupWriterFunction
from napari_hierarchical.model import Group

from ._reader import read_hdf5
from ._writer import write_hdf5

try:
    import h5py
except ModuleNotFoundError:
    h5py = None


PathLike = Union[str, os.PathLike]

available = h5py is not None
hookimpl = HookimplMarker("napari-hierarchical")


@hookimpl
def napari_hierarchical_get_group_reader(
    path: PathLike,
) -> Optional[GroupReaderFunction]:
    if available and Path(path).suffix.lower() == ".h5":
        return read_hdf5
    return None


@hookimpl
def napari_hierarchical_get_group_writer(
    path: PathLike, group: Group
) -> Optional[GroupWriterFunction]:
    if available and Path(path).suffix.lower() == ".h5":
        return write_hdf5
    return None


__all__ = [
    "available",
    "read_hdf5",
    "write_hdf5",
    "napari_hierarchical_get_group_reader",
    "napari_hierarchical_get_group_writer",
]
