import os
from typing import Callable, Optional, Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer
from pluggy import HookspecMarker

from .model import Image, Layer

PathLike = Union[str, os.PathLike]
ImageReaderFunction = Callable[[PathLike], Image]
ImageWriterFunction = Callable[[PathLike, Image], None]
LayerReaderFunction = Callable[[Layer, Viewer], NapariLayer]
LayerWriterFunction = Callable[[Layer, Viewer, NapariLayer], None]

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
def napari_bioimage_get_layer_reader(layer: Layer) -> Optional[LayerReaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_bioimage_get_layer_writer(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerWriterFunction]:
    pass
