import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_dataset.hookspecs import DatasetReaderFunction

from ._reader import read_hdf5_dataset

try:
    import h5py
except ModuleNotFoundError:
    h5py = None


PathLike = Union[str, os.PathLike]

available = h5py is not None
hookimpl = HookimplMarker("napari-dataset")


@hookimpl
def napari_dataset_get_dataset_reader(
    path: PathLike,
) -> Optional[DatasetReaderFunction]:
    if available and Path(path).suffix == ".h5":
        return read_hdf5_dataset
    return None


__all__ = ["available", "read_hdf5_dataset", "napari_dataset_get_dataset_reader"]
