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

from ._reader import load_hdf5_layer, read_hdf5_image
from ._writer import save_hdf5_layer, write_hdf5_image
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
def napari_bioimage_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    if available and isinstance(layer, HDF5Layer):
        return load_hdf5_layer
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
def napari_bioimage_get_layer_saver(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerSaverFunction]:
    # TODO
    # if available and isinstance(layer, HDF5Layer):
    #     return save_hdf5_layer
    return None


__all__ = [
    "available",
    "load_hdf5_layer",
    "read_hdf5_image",
    "save_hdf5_layer",
    "write_hdf5_image",
    "napari_bioimage_get_image_reader",
    "napari_bioimage_get_layer_loader",
    "napari_bioimage_get_image_writer",
    "napari_bioimage_get_layer_saver",
]
