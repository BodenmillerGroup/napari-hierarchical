import os
from typing import TYPE_CHECKING, Optional, Union

from napari.utils.events import EventedList
from napari.viewer import Viewer
from pluggy import PluginManager

from . import hookspecs
from ._exceptions import BioImageException
from .model import Image, Layer

if TYPE_CHECKING:
    from .widgets import QBioImageWidget

PathLike = Union[str, os.PathLike]


class BioImageController:
    def __init__(self) -> None:
        self._pm = PluginManager("napari-bioimage")
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints("napari-bioimage")
        self._viewer: Optional[Viewer] = None
        self._widget: Optional["QBioImageWidget"] = None
        self._images: EventedList[Image] = EventedList(
            basetype=Image, lookup={str: lambda image: image.name}
        )
        self._layers: EventedList[Layer] = EventedList(
            basetype=Layer, lookup={str: lambda layer: layer.name}
        )
        self._selected_layers: EventedList[Layer] = EventedList(
            basetype=Layer, lookup={str: lambda layer: layer.name}
        )

    def _get_image_reader_function(
        self, path: PathLike
    ) -> Optional[hookspecs.ImageReaderFunction]:
        image_reader_function = self._pm.hook.napari_bioimage_get_image_reader(
            path=path
        )
        return image_reader_function

    def _get_image_writer_function(
        self, path: PathLike, image: Image
    ) -> Optional[hookspecs.ImageWriterFunction]:
        image_writer_function = self._pm.hook.napari_bioimage_get_image_writer(
            path=path, image=image
        )
        return image_writer_function

    def can_read_image(self, path: PathLike) -> bool:
        return self._get_image_reader_function(path) is not None

    def can_write_image(self, path: PathLike, image: Image) -> bool:
        return self._get_image_writer_function(path, image) is not None

    def read_image(self, path: PathLike) -> Image:
        image_reader_function = self._get_image_reader_function(path)
        if image_reader_function is None:
            raise BioImageControllerException(f"No reader found for {path}")
        try:
            image = image_reader_function(path)
        except Exception as e:
            raise BioImageControllerException(e)
        self._images.append(image)
        return image

    def write_image(self, path: PathLike, image: Image) -> None:
        image_writer_function = self._get_image_writer_function(path, image)
        if image_writer_function is None:
            raise BioImageControllerException(f"No writer found for {path}")
        try:
            image_writer_function(path, image)
        except Exception as e:
            raise BioImageControllerException(e)

    def register_viewer(self, viewer: Viewer) -> None:
        assert self._viewer is None
        self._viewer = viewer

    def register_widget(self, widget: "QBioImageWidget") -> None:
        assert self._widget is None
        self._widget = widget

    @property
    def pm(self) -> PluginManager:
        return self._pm

    @property
    def viewer(self) -> Optional[Viewer]:
        return self._viewer

    @property
    def widget(self) -> Optional["QBioImageWidget"]:
        return self._widget

    @property
    def images(self) -> EventedList[Image]:
        return self._images

    @property
    def layers(self) -> EventedList[Layer]:
        return self._layers

    @property
    def selected_layers(self) -> EventedList[Layer]:
        return self._selected_layers


class BioImageControllerException(BioImageException):
    pass


controller = BioImageController()
