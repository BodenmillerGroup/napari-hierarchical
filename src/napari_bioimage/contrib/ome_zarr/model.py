from typing import TYPE_CHECKING, Sequence

from napari_bioimage.model import Layer

if TYPE_CHECKING:
    from dask.array import Array


class OMEZarrLayer(Layer):
    _data: Sequence["Array"]

    def __init__(self, *, data: Sequence["Array"], **kwargs):
        super().__init__(**kwargs)
        self._data = data

    @property
    def data(self) -> Sequence["Array"]:
        return self._data


class OMEZarrImageLayer(OMEZarrLayer):
    pass


class OMEZarrLabelsLayer(OMEZarrLayer):
    pass
