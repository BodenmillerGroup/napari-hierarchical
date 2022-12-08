import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_hierarchical.hookspecs import (
    ArrayLoaderFunction,
    ArraySaverFunction,
    GroupReaderFunction,
    GroupWriterFunction,
)
from napari_hierarchical.model import Array, Group

from ._reader import load_hdf5_array, read_hdf5_group
from ._writer import save_hdf5_array, write_hdf5_group
from .model import HDF5Array

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
        return read_hdf5_group
    return None


@hookimpl
def napari_hierarchical_get_group_writer(
    path: PathLike, group: Group
) -> Optional[GroupWriterFunction]:
    if available and Path(path).suffix.lower() == ".h5":
        return write_hdf5_group
    return None


@hookimpl
def napari_hierarchical_get_array_loader(array: Array) -> Optional[ArrayLoaderFunction]:
    if available and isinstance(array, HDF5Array):
        return load_hdf5_array
    return None


@hookimpl
def napari_hierarchical_get_array_saver(array: Array) -> Optional[ArraySaverFunction]:
    if available and isinstance(array, HDF5Array):
        return save_hdf5_array
    return None


__all__ = [
    "available",
    "read_hdf5_group",
    "write_hdf5_group",
    "load_hdf5_array",
    "save_hdf5_array",
    "napari_hierarchical_get_group_reader",
    "napari_hierarchical_get_group_writer",
    "napari_hierarchical_get_array_loader",
    "napari_hierarchical_get_array_saver",
]
