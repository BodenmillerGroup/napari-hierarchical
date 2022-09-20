from typing import List

from dask.array import Array

from napari_bioimage.model import Layer


class OMEZarrLayer(Layer):
    _data: List[Array]

    def __init__(self, *, data: List[Array], **kwargs):
        super().__init__(**kwargs)
        self._data = data

    @property
    def data(self) -> List[Array]:
        return self._data


class OMEZarrImageLayer(OMEZarrLayer):
    pass


class OMEZarrLabelsLayer(OMEZarrLayer):
    pass
