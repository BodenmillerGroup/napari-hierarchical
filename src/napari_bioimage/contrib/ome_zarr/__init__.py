import os
from pathlib import Path
from typing import Optional, Union

from napari.layers import Layer as NapariLayer
from pluggy import HookimplMarker

from napari_bioimage.hookspecs import (
    ImageReaderFunction,
    ImageWriterFunction,
    LayerLoaderFunction,
    LayerSaverFunction,
)
from napari_bioimage.model import Image, Layer

from ._exceptions import BioImageOMEZarrException
from ._reader import load_zarr_layer, read_zarr_image
from ._writer import save_zarr_layer, write_zarr_image
from .model import ZarrLayer

available: bool = True
try:
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Multiscales
except ModuleNotFoundError:
    available = False


PathLike = Union[str, os.PathLike]

hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    if Path(path).suffix == ".zarr":
        zarr_location = ZarrLocation(str(path))
        if zarr_location.exists() and Multiscales.matches(zarr_location):
            return read_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    if isinstance(layer, ZarrLayer):
        return load_zarr_layer
    return None


@hookimpl
def napari_bioimage_get_image_writer(
    path: PathLike, image: Image
) -> Optional[ImageWriterFunction]:
    if Path(path).suffix == ".zarr":
        return write_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_saver(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerSaverFunction]:
    if isinstance(layer, ZarrLayer):
        return save_zarr_layer
    return None


__all__ = [
    "available",
    "load_zarr_layer",
    "read_zarr_image",
    "save_zarr_layer",
    "write_zarr_image",
    "BioImageOMEZarrException",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_loader",
    "napari_bioimage_get_image_writer",
    "napari_bioimage_get_layer_saver",
]
