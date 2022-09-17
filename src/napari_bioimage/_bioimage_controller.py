import os
from typing import List, Sequence, Union

from .model import Image

PathLike = Union[str, os.PathLike]


class BioImageController:
    def __init__(self) -> None:
        self._images: List[Image] = []

    def open(self, path: PathLike) -> None:
        pass  # TODO

    @property
    def images(self) -> Sequence[Image]:
        return self._images

    def append_image(self, image: Image) -> None:
        self.insert_image(len(self._images), image)

    def insert_image(self, index: int, image: Image) -> None:
        self._images.insert(index, image)

    def remove_image(self, image: Image) -> None:
        self._images.remove(image)
