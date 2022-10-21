import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_bioimage.hookspecs import ReaderFunction, WriterFunction
from napari_bioimage.model import Image

from ._reader import read_ome_zarr
from ._writer import write_ome_zarr

try:
    import ome_zarr
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Multiscales
except ModuleNotFoundError:
    ome_zarr = None


PathLike = Union[str, os.PathLike]

available = ome_zarr is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    if available and Path(path).suffix == ".zarr":
        zarr_location = ZarrLocation(str(path))
        if zarr_location.exists() and Multiscales.matches(zarr_location):
            return read_ome_zarr
    return None


@hookimpl
def napari_bioimage_get_writer(
    path: PathLike, image: Image
) -> Optional[WriterFunction]:
    # TODO
    # if available and Path(path).suffix == ".zarr":
    #     return write_ome_zarr
    return None


__all__ = [
    "available",
    "read_ome_zarr",
    "write_ome_zarr",
    "napari_bioimage_get_reader",
    "napari_bioimage_get_writer",
]
