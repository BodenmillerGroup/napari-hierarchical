from typing import List, Optional, Sequence

from ._layer import Layer


class Image:
    def __init__(self, name: str, parent: Optional["Image"] = None) -> None:
        self._name = name
        self._parent = parent
        self._children: List[Image] = []
        self._layers: List[Layer] = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def parent(self) -> Optional["Image"]:
        return self._parent

    @parent.setter
    def parent(self, value: Optional["Image"]) -> None:
        self._parent = value

    @property
    def layers(self) -> Sequence[Layer]:
        return self._layers

    def append_layer(self, layer: Layer) -> None:
        self.insert_layer(len(self._layers), layer)

    def insert_layer(self, index: int, layer: Layer) -> None:
        self._layers.insert(index, layer)

    def remove_layer(self, layer: Layer) -> None:
        self._layers.remove(layer)
