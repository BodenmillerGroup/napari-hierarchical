from napari.layers import Image as NapariImageLayer
from napari.layers import Layer as NapariLayer

from napari_dataset.model import Layer

try:
    import dask.array as da
    import h5py
except ModuleNotFoundError:
    da = None
    h5py = None


class HDF5Layer(Layer):
    hdf5_file: str
    path: str

    def load(self) -> NapariLayer:
        with h5py.File(self.hdf5_file) as f:
            data = da.from_array(f[self.path])
        napari_layer = NapariImageLayer(name=self.name, data=data)
        return napari_layer

    def save(self) -> None:
        raise NotImplementedError()  # TODO
