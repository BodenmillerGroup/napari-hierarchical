import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_bioimage.hookspecs import ReaderFunction, WriterFunction
from napari_bioimage.model import Image

from ._reader import read_hdf5
from ._writer import write_hdf5

try:
    import h5py
except ModuleNotFoundError:
    h5py = None


PathLike = Union[str, os.PathLike]

available = h5py is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    if available and Path(path).suffix == ".h5":
        return read_hdf5
    return None


@hookimpl
def napari_bioimage_get_writer(
    path: PathLike, image: Image
) -> Optional[WriterFunction]:
    # TODO
    # if available and Path(path).suffix == ".h5":
    #     return write_hdf5
    return None


__all__ = [
    "available",
    "read_hdf5",
    "write_hdf5",
    "napari_bioimage_get_reader",
    "napari_bioimage_get_writer",
]
