from napari.layers import Image as NapariImageLayer
from napari.layers import Layer as NapariLayer

from napari_bioimage.model import Layer

try:
    import dask.array as da
    import zarr
except ModuleNotFoundError:
    da = None
    zarr = None


class ZarrLayer(Layer):
    zarr_file: str
    path: str

    def load(self) -> NapariLayer:
        z = zarr.open(store=self.zarr_file, mode="r")
        data = da.from_zarr(z[self.path])
        napari_layer = NapariImageLayer(name=self.name, data=data)
        return napari_layer

    def save(self) -> None:
        raise NotImplementedError()  # TODO
