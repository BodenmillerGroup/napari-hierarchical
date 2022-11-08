import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_dataset.hookspecs import DatasetReaderFunction

from ._reader import read_ome_zarr_dataset

try:
    import ome_zarr
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Multiscales
except ModuleNotFoundError:
    ome_zarr = None


PathLike = Union[str, os.PathLike]

available = ome_zarr is not None
hookimpl = HookimplMarker("napari-dataset")


@hookimpl
def napari_dataset_get_dataset_reader(
    path: PathLike,
) -> Optional[DatasetReaderFunction]:
    if available and Path(path).suffix == ".zarr":
        zarr_location = ZarrLocation(str(path))
        if zarr_location.exists() and Multiscales.matches(zarr_location):
            return read_ome_zarr_dataset
    return None


__all__ = ["available", "read_ome_zarr_dataset", "napari_dataset_get_dataset_reader"]
