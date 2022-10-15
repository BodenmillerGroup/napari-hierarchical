import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_bioimage.hookspecs import ImageReaderFunction, LayerReaderFunction
from napari_bioimage.model import Layer

from ._reader import read_imc_image, read_imc_layer
from .model import IMCLayer

try:
    import readimc
except ModuleNotFoundError:
    readimc = None


PathLike = Union[str, os.PathLike]

available: bool = readimc is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    if available and Path(path).suffix == ".mcd":
        return read_imc_image
    return None


@hookimpl
def napari_bioimage_get_layer_reader(layer: Layer) -> Optional[LayerReaderFunction]:
    if available and isinstance(layer, IMCLayer):
        return read_imc_layer
    return None


__all__ = [
    "available",
    "read_imc_image",
    "read_imc_layer",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_reader",
]
