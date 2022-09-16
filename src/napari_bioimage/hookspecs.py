import os
from typing import Callable, Optional, Union

import pluggy
from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from .model import Image, Layer

PathLike = Union[str, os.PathLike]

ImageReaderFunction = Callable[[PathLike], Image]
LayerLoaderFunction = Callable[[Viewer, Layer], NapariLayer]

ImageWriterFunction = Callable[[PathLike, Image], None]
LayerSaverFunction = Callable[[Viewer, Layer, NapariLayer], None]

hookspec = pluggy.HookspecMarker("napari-bioimage")


@hookspec
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    pass


@hookspec
def napari_bioimage_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    pass


@hookspec
def napari_bioimage_get_image_writer(
    path: PathLike, image: Image
) -> Optional[ImageWriterFunction]:
    pass


@hookspec
def napari_bioimage_get_layer_saver(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerSaverFunction]:
    pass
