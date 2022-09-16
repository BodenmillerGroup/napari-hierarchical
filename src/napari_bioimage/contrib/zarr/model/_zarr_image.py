from ome_zarr.io import ZarrLocation

from napari_bioimage.data import Image


class ZarrImage(Image):
    def __init__(self, zarr_location: ZarrLocation) -> None:
        super().__init__(zarr_location.basename())
        self._zarr_location = zarr_location

    @property
    def zarr_location(self) -> ZarrLocation:
        return self._zarr_location
