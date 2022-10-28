import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_dataset.contrib.imc.model import IMCAcquisitionLayer, IMCPanoramaLayer
from napari_dataset.hookspecs import DatasetReaderFunction, LayerLoaderFunction
from napari_dataset.model import Layer

from ._reader import (
    load_imc_acquisition_layer,
    load_imc_panorama_layer,
    read_imc_dataset,
)

try:
    import readimc
except ModuleNotFoundError:
    readimc = None


PathLike = Union[str, os.PathLike]

available = readimc is not None
hookimpl = HookimplMarker("napari-dataset")


@hookimpl
def napari_dataset_get_dataset_reader(
    path: PathLike,
) -> Optional[DatasetReaderFunction]:
    if available and Path(path).suffix == ".mcd":
        return read_imc_dataset
    return None


@hookimpl
def napari_dataset_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    x = layer
    if (
        available
        and isinstance(x, IMCPanoramaLayer)
        and x.dataset == x.panorama_dataset
        and x.panorama_dataset.parent == x.panorama_dataset.panoramas_dataset
        and (
            x.panorama_dataset.panoramas_dataset.parent
            == x.panorama_dataset.panoramas_dataset.slide_dataset
        )
        and (
            x.panorama_dataset.panoramas_dataset.slide_dataset.parent
            == x.panorama_dataset.panoramas_dataset.slide_dataset.imc_dataset
        )
        and (
            x.panorama_dataset.panoramas_dataset.slide_dataset.imc_dataset.parent
            is None
        )
    ):
        return load_imc_panorama_layer
    if (
        available
        and isinstance(x, IMCAcquisitionLayer)
        and x.dataset == x.acquisition_dataset
        and x.acquisition_dataset.parent == x.acquisition_dataset.acquisitions_dataset
        and (
            x.acquisition_dataset.acquisitions_dataset.parent
            == x.acquisition_dataset.acquisitions_dataset.slide_dataset
        )
        and (
            x.acquisition_dataset.acquisitions_dataset.slide_dataset.parent
            == x.acquisition_dataset.acquisitions_dataset.slide_dataset.imc_dataset
        )
        and (
            x.acquisition_dataset.acquisitions_dataset.slide_dataset.imc_dataset.parent
            is None
        )
    ):
        return load_imc_acquisition_layer
    return None


__all__ = [
    "available",
    "read_imc_dataset",
    "load_imc_panorama_layer",
    "load_imc_acquisition_layer",
    "napari_dataset_get_dataset_reader",
    "napari_dataset_get_layer_loader",
]
