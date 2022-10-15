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

from ._reader import read_ome_zarr_image, read_ome_zarr_layer
from ._writer import write_ome_zarr_image, write_ome_zarr_layer
from .model import OMEZarrLayer

try:
    import ome_zarr
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Multiscales
except ModuleNotFoundError:
    ome_zarr = None


PathLike = Union[str, os.PathLike]

available: bool = ome_zarr is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    if available and Path(path).suffix == ".zarr":
        zarr_location = ZarrLocation(str(path))
        if zarr_location.exists() and Multiscales.matches(zarr_location):
            return read_ome_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_reader(layer: Layer) -> Optional[LayerReaderFunction]:
    if available and isinstance(layer, OMEZarrLayer):
        return read_ome_zarr_layer
    return None


@hookimpl
def napari_bioimage_get_image_writer(
    path: PathLike, image: Image
) -> Optional[ImageWriterFunction]:
    # TODO
    # if available and Path(path).suffix == ".zarr":
    #     return write_ome_zarr_image
    return None


@hookimpl
def napari_bioimage_get_layer_writer(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerWriterFunction]:
    # TODO
    # if available and isinstance(layer, OMEZarrLayer):
    #     return save_ome_zarr_layer
    return None


__all__ = [
    "available",
    "read_ome_zarr_image",
    "read_ome_zarr_layer",
    "write_ome_zarr_image",
    "write_ome_zarr_layer",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_reader",
    "napari_bioimage_get_image_writer",
    "napari_bioimage_get_layer_writer",
]
