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

from ._reader import load_zarr_layer, read_zarr_image
from ._writer import save_zarr_layer, write_zarr_image
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
    if available and Path(path).suffix == ".zarr":
        return read_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    if available and isinstance(layer, ZarrLayer):
        return load_zarr_layer
    return None


@hookimpl
def napari_bioimage_get_image_writer(
    path: PathLike, image: Image
) -> Optional[ImageWriterFunction]:
    # TODO
    # if available and Path(path).suffix == ".zarr":
    #     return write_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_saver(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerSaverFunction]:
    # TODO
    # if available and isinstance(layer, ZarrLayer):
    #     return save_zarr_layer
    return None


__all__ = [
    "available",
    "load_zarr_layer",
    "read_zarr_image",
    "save_zarr_layer",
    "write_zarr_image",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_loader",
    "napari_bioimage_get_image_writer",
    "napari_bioimage_get_layer_saver",
]
