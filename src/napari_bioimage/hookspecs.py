import os
from typing import Callable, Optional, Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer
from pluggy import HookspecMarker

from .model import Image, Layer

PathLike = Union[str, os.PathLike]
ImageReaderFunction = Callable[[PathLike], Image]
ImageWriterFunction = Callable[[PathLike, Image], None]
LayerLoaderFunction = Callable[[Layer, Viewer], NapariLayer]
LayerSaverFunction = Callable[[Layer, Viewer, NapariLayer], None]

hookspec = HookspecMarker("napari-bioimage")


@hookspec(firstresult=True)
def napari_bioimage_get_image_reader(path: PathLike) -> Optional[ImageReaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_bioimage_get_image_writer(
    path: PathLike, image: Image
) -> Optional[ImageWriterFunction]:
    pass


@hookspec(firstresult=True)
def napari_bioimage_get_layer_loader(
    layer: Layer,
) -> Optional[LayerLoaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_bioimage_get_layer_saver(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerSaverFunction]:
    pass
