from typing import TYPE_CHECKING, List, Optional, Sequence

from ._layer import Layer

if TYPE_CHECKING:
    from ._group import Group


class Image:
    def __init__(self, name: str, group: Optional["Group"] = None) -> None:
        self._name = name
        self._group = group
        self._layers: List[Layer] = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def group(self) -> Optional["Group"]:
        return self._group

    @group.setter
    def group(self, value: Optional["Group"]) -> None:
        self._group = value

    @property
    def layers(self) -> Sequence[Layer]:
        return self._layers

    def append_layer(self, layer: Layer) -> None:
        self.insert_layer(len(self._layers), layer)

    def insert_layer(self, index: int, layer: Layer) -> None:
        self._layers.insert(index, layer)

    def remove_layer(self, layer: Layer) -> None:
        self._layers.remove(layer)
