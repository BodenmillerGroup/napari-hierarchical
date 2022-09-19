from typing import List

from dask.array import Array

from napari_bioimage.model import Layer


class ZarrLayer(Layer):
    _data: List[Array]

    def __init__(self, *, data: List[Array], **kwargs):
        super().__init__(**kwargs)
        self._data = data

    @property
    def data(self) -> List[Array]:
        return self._data


class ZarrImageLayer(ZarrLayer):
    pass


class ZarrLabelsLayer(ZarrLayer):
    pass
