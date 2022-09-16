import os
from pathlib import Path
from typing import Optional, Union

import pluggy
from napari.layers import Layer as NapariLayer
from ome_zarr.io import ZarrLocation

from napari_bioimage.data import Image, Layer
from napari_bioimage.hookspecs import (
    ImageReaderFunction,
    ImageWriterFunction,
    LayerLoaderFunction,
    LayerSaverFunction,
)

from .data import ZarrLayer
from .reader import load_zarr_layer, read_zarr_image
from .writer import save_zarr_layer, write_zarr_image

PathLike = Union[str, os.PathLike]

hookimpl = pluggy.HookimplMarker("napari-bioimage.contrib.zarr")


@hookimpl
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    if not isinstance(path, str) and not isinstance(path, Path):
        path = str(path)
    zarr_location = ZarrLocation(path)
    if zarr_location.exists():
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
