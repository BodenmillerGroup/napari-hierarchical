import os
from typing import Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, Layer

PathLike = Union[str, os.PathLike]


def write_ome_zarr_image(path: PathLike, image: Image) -> None:
    raise NotImplementedError()  # TODO


def save_ome_zarr_layer(
    layer: Layer, viewer: Viewer, napari_layer: NapariLayer
) -> None:
    raise NotImplementedError()  # TODO
