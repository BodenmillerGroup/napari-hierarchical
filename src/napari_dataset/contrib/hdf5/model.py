from napari_dataset.model import Layer


class HDF5Layer(Layer):
    hdf5_file: str
    hdf5_path: str
