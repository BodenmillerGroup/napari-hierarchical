from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from ._image import Image


class Layer:
    def __init__(self, name: str, image: Optional["Image"] = None) -> None:
        self._name = name
        self._image = image
        self._metadata: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def image(self) -> Optional["Image"]:
        return self._image

    @image.setter
    def image(self, value: Optional["Image"]) -> None:
        self._image = value

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
