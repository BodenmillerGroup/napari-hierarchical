import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_dataset.hookspecs import ReaderFunction, WriterFunction
from napari_dataset.model import Dataset

from ._reader import read_zarr
from ._writer import write_zarr

try:
    import zarr
except ModuleNotFoundError:
    zarr = None


PathLike = Union[str, os.PathLike]

available = zarr is not None
hookimpl = HookimplMarker("napari-dataset")


@hookimpl
def napari_dataset_get_reader(path: PathLike) -> Optional[ReaderFunction]:
    if available and any(part.endswith(".zarr") for part in Path(path).parts):
        return read_zarr
    return None


@hookimpl
def napari_dataset_get_writer(
    path: PathLike, dataset: Dataset
) -> Optional[WriterFunction]:
    # TODO
    # if available and any(part.endswith(".zarr") for part in Path(path).parts):
    #     return write_zarr
    return None


__all__ = [
    "available",
    "read_zarr",
    "write_zarr",
    "napari_dataset_get_reader",
    "napari_dataset_get_writer",
]
