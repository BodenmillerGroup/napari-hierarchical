from typing import TYPE_CHECKING, List

import dask.array as da

from napari_bioimage.data import Layer

if TYPE_CHECKING:
    from ._zarr_image import ZarrImage


class ZarrLayer(Layer):
    def __init__(
        self,
        name: str,
        image: "ZarrImage",
        data: List[da.Array],
    ) -> None:
        super().__init__(name, image=image)
        self._data = data

    @property
    def data(self) -> List[da.Array]:
        return self._data
