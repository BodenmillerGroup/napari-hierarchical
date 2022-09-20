import os
from typing import Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, Layer

PathLike = Union[str, os.PathLike]


def read_imc_image(path: PathLike) -> Image:
    raise NotImplementedError()  # TODO


def load_imc_layer(layer: Layer, viewer: Viewer) -> NapariLayer:
    raise NotImplementedError()  # TODO
