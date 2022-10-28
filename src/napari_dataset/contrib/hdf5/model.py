from typing import Optional, Tuple

from napari_dataset.model import Dataset, Layer


class HDF5Dataset(Dataset):
    hdf5_file: str

    @staticmethod
    def get_root(dataset: Dataset) -> Tuple[Optional["HDF5Dataset"], str]:
        dataset_names = []
        while dataset.parent is not None or (
            dataset is not None and not isinstance(dataset, HDF5Dataset)
        ):
            dataset_names.append(dataset.name)
            dataset = dataset.parent
        return dataset, "/".join(reversed(dataset_names))


class HDF5Layer(Layer):
    root_hdf5_dataset: HDF5Dataset
