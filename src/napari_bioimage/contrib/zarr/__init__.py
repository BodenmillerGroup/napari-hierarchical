import os
from pathlib import Path
from typing import Optional, Union

from napari.layers import Layer as NapariLayer
from pluggy import HookimplMarker

from napari_bioimage.hookspecs import (
    ImageReaderFunction,
    ImageWriterFunction,
    LayerReaderFunction,
    LayerWriterFunction,
)
from napari_bioimage.model import Image, Layer

from ._reader import read_zarr_image, read_zarr_layer
from ._writer import write_zarr_image, write_zarr_layer
from .model import ZarrLayer

try:
    import zarr
except ModuleNotFoundError:
    zarr = None


PathLike = Union[str, os.PathLike]

available: bool = zarr is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    if available and any(part.endswith(".zarr") for part in Path(path).parts):
        return read_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_reader(layer: Layer) -> Optional[LayerReaderFunction]:
    if available and isinstance(layer, ZarrLayer):
        return read_zarr_layer
    return None


@hookimpl
def napari_bioimage_get_image_writer(
    path: PathLike, image: Image
) -> Optional[ImageWriterFunction]:
    # TODO
    # if available and any(part.endswith(".zarr") for part in Path(path).parts):
    #     return write_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_writer(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerWriterFunction]:
    # TODO
    # if available and isinstance(layer, ZarrLayer):
    #     return save_zarr_layer
    return None


__all__ = [
    "available",
    "read_zarr_image",
    "read_zarr_layer",
    "write_zarr_image",
    "write_zarr_layer",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_reader",
    "napari_bioimage_get_image_writer",
    "napari_bioimage_get_layer_writer",
]
