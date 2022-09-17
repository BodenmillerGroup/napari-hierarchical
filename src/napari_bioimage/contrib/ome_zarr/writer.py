import os
from typing import Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, Layer

PathLike = Union[str, os.PathLike]


def write_zarr_image(path: PathLike, image: Image) -> None:
    pass


def save_zarr_layer(viewer: Viewer, layer: Layer, napari_layer: NapariLayer) -> None:
    pass
