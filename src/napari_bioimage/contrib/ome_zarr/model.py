from typing import Sequence

from dask.array import Array

from napari_bioimage.model import Image, Layer


class OMEZarrImage(Image):
    zarr_file: str


class OMEZarrLayer(Layer):
    _data: Sequence[Array]

    def __init__(self, *, data: Sequence[Array], **kwargs):
        super().__init__(**kwargs)
        self._data = data

    @property
    def data(self) -> Sequence[Array]:
        return self._data


class OMEZarrImageLayer(OMEZarrLayer):
    pass


class OMEZarrLabelsLayer(OMEZarrLayer):
    pass
