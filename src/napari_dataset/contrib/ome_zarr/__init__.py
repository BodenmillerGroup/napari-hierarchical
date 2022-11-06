import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_dataset.contrib.ome_zarr.model import OMEZarrImageLayer, OMEZarrLabelsLayer
from napari_dataset.hookspecs import (
    DatasetReaderFunction,
    DatasetWriterFunction,
    LayerLoaderFunction,
    LayerSaverFunction,
)
from napari_dataset.model import Dataset, Layer

from ._reader import (
    load_ome_zarr_image_layer,
    load_ome_zarr_labels_layer,
    read_ome_zarr_dataset,
)
from ._writer import (
    save_ome_zarr_image_layer,
    save_ome_zarr_labels_layer,
    write_ome_zarr_dataset,
)

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


@hookimpl
def napari_dataset_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    if (
        available
        and isinstance(layer, OMEZarrImageLayer)
        and layer.get_parent() == layer.ome_zarr_dataset
        and layer.ome_zarr_dataset.get_parent() is None
    ):
        return load_ome_zarr_image_layer
    if (
        available
        and isinstance(layer, OMEZarrLabelsLayer)
        and layer.get_parent() == layer.ome_zarr_dataset
        and layer.ome_zarr_dataset.get_parent() is None
    ):
        return load_ome_zarr_labels_layer
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
    "read_ome_zarr_dataset",
    "load_ome_zarr_image_layer",
    "load_ome_zarr_labels_layer",
    "write_ome_zarr_dataset",
    "save_ome_zarr_image_layer",
    "save_ome_zarr_labels_layer",
    "napari_dataset_get_dataset_reader",
    "napari_dataset_get_dataset_writer",
]
