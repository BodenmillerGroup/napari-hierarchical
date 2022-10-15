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

from ._reader import read_hdf5_image, read_hdf5_layer
from ._writer import write_hdf5_image, write_hdf5_layer
from .model import HDF5Layer

try:
    import h5py
except ModuleNotFoundError:
    h5py = None


PathLike = Union[str, os.PathLike]

available: bool = h5py is not None
hookimpl = HookimplMarker("napari-bioimage")


@hookimpl
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    if available and Path(path).suffix == ".h5":
        return read_hdf5_image
    return None


@hookimpl
def napari_bioimage_get_layer_reader(layer: Layer) -> Optional[LayerReaderFunction]:
    if available and isinstance(layer, HDF5Layer):
        return read_hdf5_layer
    return None


@hookimpl
def napari_bioimage_get_image_writer(
    path: PathLike, image: Image
) -> Optional[ImageWriterFunction]:
    # TODO
    # if available and Path(path).suffix == ".h5":
    #     return write_hdf5_image
    return None


@hookimpl
def napari_bioimage_get_layer_writer(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerWriterFunction]:
    # TODO
    # if available and isinstance(layer, HDF5Layer):
    #     return save_hdf5_layer
    return None


__all__ = [
    "available",
    "read_hdf5_image",
    "read_hdf5_layer",
    "write_hdf5_image",
    "write_hdf5_layer",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_reader",
    "napari_bioimage_get_image_writer",
    "napari_bioimage_get_layer_writer",
]
