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

from ._reader import load_zarr_array, read_zarr_group
from ._writer import save_zarr_array, write_zarr_group
from .model import ZarrArray

try:
    import zarr
except ModuleNotFoundError:
    zarr = None


PathLike = Union[str, os.PathLike]

available = zarr is not None
hookimpl = HookimplMarker("napari-hierarchical")


@hookimpl
def napari_hierarchical_get_group_reader(
    path: PathLike,
) -> Optional[GroupReaderFunction]:
    if available and Path(path).suffix.lower() == ".zarr":
        return read_zarr_group
    return None


@hookimpl
def napari_hierarchical_get_group_writer(
    path: PathLike, group: Group
) -> Optional[GroupWriterFunction]:
    if available and Path(path).suffix.lower() == ".zarr":
        return write_zarr_group
    return None


@hookimpl
def napari_hierarchical_get_array_loader(array: Array) -> Optional[ArrayLoaderFunction]:
    if available and isinstance(array, ZarrArray):
        return load_zarr_array
    return None


@hookimpl
def napari_hierarchical_get_array_saver(array: Array) -> Optional[ArraySaverFunction]:
    if available and isinstance(array, ZarrArray):
        return save_zarr_array
    return None


__all__ = [
    "available",
    "read_zarr_group",
    "write_zarr_group",
    "load_zarr_array",
    "save_zarr_array",
    "napari_hierarchical_get_group_reader",
    "napari_hierarchical_get_group_writer",
    "napari_hierarchical_get_array_loader",
    "napari_hierarchical_get_array_saver",
]
