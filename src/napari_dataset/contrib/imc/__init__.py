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
    if available and isinstance(layer, IMCPanoramaLayer):
        panorama_dataset = layer._panorama_dataset
        if layer.get_parent() != panorama_dataset:
            return None
        panoramas_dataset = panorama_dataset._panoramas_dataset
        if panorama_dataset.get_parent() != panoramas_dataset:
            return None
        slide_dataset = panoramas_dataset._slide_dataset
        if panoramas_dataset.get_parent() != slide_dataset:
            return None
        imc_dataset = slide_dataset._imc_dataset
        if (
            slide_dataset.get_parent() != imc_dataset
            or imc_dataset.get_parent() is not None
        ):
            return None
        return load_imc_panorama_layer
    if available and isinstance(layer, IMCAcquisitionLayer):
        acquisition_dataset = layer._acquisition_dataset
        if layer.get_parent() != acquisition_dataset:
            return None
        acquisitions_dataset = acquisition_dataset._acquisitions_dataset
        if acquisition_dataset.get_parent() != acquisitions_dataset:
            return None
        slide_dataset = acquisitions_dataset._slide_dataset
        if acquisitions_dataset.get_parent() != slide_dataset:
            return None
        imc_dataset = slide_dataset._imc_dataset
        if (
            slide_dataset.get_parent() != imc_dataset
            or imc_dataset.get_parent() is not None
        ):
            return None
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
