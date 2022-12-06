import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_hierarchical.hookspecs import GroupReaderFunction, GroupWriterFunction
from napari_hierarchical.model import Group

from ._reader import read_zarr
from ._writer import write_zarr

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
        return read_zarr
    return None


@hookimpl
def napari_hierarchical_get_group_writer(
    path: PathLike, group: Group
) -> Optional[GroupWriterFunction]:
    if available and Path(path).suffix.lower() == ".zarr":
        return write_zarr
    return None


__all__ = [
    "available",
    "read_zarr",
    "write_zarr",
    "napari_hierarchical_get_group_reader",
    "napari_hierarchical_get_group_writer",
]
