import os
from pathlib import Path
from typing import Optional, Union

from pluggy import HookimplMarker

from napari_bioimage.hookspecs import ImageReaderFunction, LayerLoaderFunction
from napari_bioimage.model import Layer

from ._reader import load_imc_layer, read_imc_image
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
def napari_bioimage_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    if available and isinstance(layer, IMCLayer):
        return load_imc_layer
    return None


__all__ = [
    "available",
    "load_imc_layer",
    "read_imc_image",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_loader",
]
