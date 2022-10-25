import os
from typing import Optional, Union

from napari.utils.events import EventedList
from napari.viewer import Viewer
from pluggy import PluginManager

from . import hookspecs
from ._exceptions import BioImageException
from .model import Image, Layer

PathLike = Union[str, os.PathLike]


class BioImageController:
    def __init__(self) -> None:
        self._pm = PluginManager("napari-bioimage")
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints("napari-bioimage")
        self._viewer: Optional[Viewer] = None
        self._images: EventedList[Image] = EventedList(
            basetype=Image, lookup={str: lambda image: image.name}
        )
        self._layers: EventedList[Layer] = EventedList(
            basetype=Layer, lookup={str: lambda layer: layer.name}
        )

    def _get_reader_function(
        self, path: PathLike
    ) -> Optional[hookspecs.ReaderFunction]:
        reader_function = self._pm.hook.napari_bioimage_get_reader(path=path)
        return reader_function

    def _get_writer_function(
        self, path: PathLike, image: Image
    ) -> Optional[hookspecs.WriterFunction]:
        writer_function = self._pm.hook.napari_bioimage_get_writer(
            path=path, image=image
        )
        return writer_function

    def can_read(self, path: PathLike) -> bool:
        reader_function = self._get_reader_function(path)
        return reader_function is not None

    def can_write(self, path: PathLike, image: Image) -> bool:
        writer_function = self._get_writer_function(path, image)
        return writer_function is not None

    def read(self, path: PathLike) -> Image:
        reader_function = self._get_reader_function(path)
        if reader_function is None:
            raise BioImageControllerException(f"No reader found for {path}")
        try:
            image = reader_function(path)
        except Exception as e:
            raise BioImageControllerException(e)
        layers = image.get_layers(recursive=True)
        self._images.append(image)
        self._layers += layers
        return image

    def write(self, path: PathLike, image: Image) -> None:
        writer_function = self._get_writer_function(path, image)
        if writer_function is None:
            raise BioImageControllerException(f"No writer found for {path}")
        try:
            writer_function(path, image)
        except Exception as e:
            raise BioImageControllerException(e)

    def register_viewer(self, viewer: Viewer) -> None:
        assert self._viewer is None
        self._viewer = viewer

    @property
    def pm(self) -> PluginManager:
        return self._pm

    @property
    def viewer(self) -> Optional[Viewer]:
        return self._viewer

    @property
    def images(self) -> EventedList[Image]:
        return self._images

    @property
    def layers(self) -> EventedList[Layer]:
        return self._layers


class BioImageControllerException(BioImageException):
    pass


controller = BioImageController()
