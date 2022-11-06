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

from ._reader import load_zarr_layer, read_zarr_dataset
from ._writer import save_zarr_layer, write_zarr_dataset
from .model import ZarrLayer

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


@hookimpl
def napari_dataset_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    if available and isinstance(layer, ZarrLayer):
        return load_zarr_layer
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
    "read_zarr_dataset",
    "load_zarr_layer",
    "write_zarr_dataset",
    "save_zarr_layer",
    "napari_dataset_get_dataset_reader",
    "napari_dataset_get_layer_loader",
    "napari_dataset_get_dataset_writer",
    "napari_dataset_get_layer_saver",
]
