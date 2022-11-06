import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_dataset.hookspecs import (
    DatasetReaderFunction,
    DatasetWriterFunction,
    LayerLoaderFunction,
    LayerSaverFunction,
)
from napari_dataset.model import Dataset, Layer

from ._reader import load_hdf5_layer, read_hdf5_dataset
from ._writer import save_hdf5_layer, write_hdf5_dataset
from .model import HDF5Layer

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


@hookimpl
def napari_dataset_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    if available and isinstance(layer, HDF5Layer):
        dataset = layer.get_parent()
        assert dataset is not None
        if dataset.get_root()[0] == layer.root_hdf5_dataset:
            return load_hdf5_layer
    return None


@hookimpl
def napari_dataset_get_dataset_writer(
    path: PathLike, dataset: Dataset
) -> Optional[DatasetWriterFunction]:
    return None  # TODO


@hookimpl
def napari_dataset_get_layer_saver(layer: Layer) -> Optional[LayerSaverFunction]:
    return None  # TODO


__all__ = [
    "available",
    "read_hdf5_dataset",
    "load_hdf5_layer",
    "write_hdf5_dataset",
    "save_hdf5_layer",
    "napari_dataset_get_dataset_reader",
    "napari_dataset_get_layer_loader",
    "napari_dataset_get_dataset_writer",
    "napari_dataset_get_layer_saver",
]
