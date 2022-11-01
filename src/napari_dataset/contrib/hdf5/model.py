from napari_dataset.model import Dataset, Layer


class HDF5Dataset(Dataset):
    hdf5_file: str


class HDF5Layer(Layer):
    root_hdf5_dataset: HDF5Dataset
