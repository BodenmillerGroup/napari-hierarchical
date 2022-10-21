import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_bioimage.hookspecs import ReaderFunction, WriterFunction
from napari_bioimage.model import Image

from ._reader import read_zarr
from ._writer import write_zarr

try:
    import zarr
except ModuleNotFoundError:
    zarr = None


PathLike = Union[str, os.PathLike]

available = zarr is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    if available and any(part.endswith(".zarr") for part in Path(path).parts):
        return read_zarr
    return None


@hookimpl
def napari_bioimage_get_writer(
    path: PathLike, image: Image
) -> Optional[WriterFunction]:
    # TODO
    # if available and any(part.endswith(".zarr") for part in Path(path).parts):
    #     return write_zarr_image
    return None


__all__ = [
    "available",
    "read_zarr",
    "write_zarr",
    "napari_bioimage_get_reader",
    "napari_bioimage_get_writer",
]
