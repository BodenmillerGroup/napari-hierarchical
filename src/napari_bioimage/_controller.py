import os
from typing import Optional, Union

from napari.utils.events import EventedList

from ._exceptions import BioImageException
from ._plugins import pm
from .hookspecs import ImageReaderFunction, ImageWriterFunction
from .model import Image

PathLike = Union[str, os.PathLike]


class BioImageControllerException(BioImageException):
    pass


class BioImageController:
    def __init__(self) -> None:
        self._images: EventedList[Image] = EventedList(
            basetype=Image, lookup={str: lambda image: image.name}
        )

    def _get_image_reader_function(
        self, path: PathLike
    ) -> Optional[ImageReaderFunction]:
        image_reader_function = pm.hook.napari_bioimage_get_image_reader(path=path)
        return image_reader_function

    def _get_image_writer_function(
        self, path: PathLike, image: Image
    ) -> Optional[ImageWriterFunction]:
        image_writer_function = pm.hook.napari_bioimage_get_image_writer(
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
        image = image_reader_function(path)
        self._images.append(image)
        return image

    def write_image(self, path: PathLike, image: Image) -> None:
        image_writer_function = self._get_image_writer_function(path, image)
        if image_writer_function is None:
            raise BioImageControllerException(f"No writer found for {path}")
        image_writer_function(path, image)

    @property
    def images(self) -> EventedList[Image]:
        return self._images


controller = BioImageController()
