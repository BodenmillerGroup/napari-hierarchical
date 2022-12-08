from napari_hierarchical.model import Array


class HDF5Array(Array):
    hdf5_file: str
    hdf5_path: str
