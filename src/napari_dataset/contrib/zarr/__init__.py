import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_dataset.hookspecs import DatasetReaderFunction

from ._reader import read_zarr_dataset

try:
    import zarr
except ModuleNotFoundError:
    zarr = None


PathLike = Union[str, os.PathLike]

available = zarr is not None
hookimpl = HookimplMarker("napari-dataset")


@hookimpl
def napari_dataset_get_dataset_reader(
    path: PathLike,
) -> Optional[DatasetReaderFunction]:
    if available and Path(path).suffix == ".zarr":
        return read_zarr_dataset
    return None


__all__ = ["available", "read_zarr_dataset", "napari_dataset_get_dataset_reader"]
