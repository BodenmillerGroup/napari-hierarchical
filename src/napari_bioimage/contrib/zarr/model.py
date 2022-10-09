from typing import TYPE_CHECKING

from napari_bioimage.model import Layer

if TYPE_CHECKING:
    from dask.array import Array


class ZarrLayer(Layer):
    _data: "Array"

    def __init__(self, *, data: "Array", **kwargs):
        super().__init__(**kwargs)
        self._data = data

    @property
    def data(self) -> "Array":
        return self._data
