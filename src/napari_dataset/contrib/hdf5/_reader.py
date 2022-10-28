import os
from pathlib import Path
from typing import Union

from napari.layers import Image as NapariImageLayer
from napari.layers import Layer as NapariLayer

from napari_dataset.model import Dataset, Layer

from .model import HDF5Dataset, HDF5Layer

try:
    import dask.array as da
    import h5py
except ModuleNotFoundError:
    da = None
    h5py = None

PathLike = Union[str, os.PathLike]


def read_hdf5_dataset(path: PathLike) -> Dataset:
    hdf5_dataset = HDF5Dataset(name=Path(path).name, hdf5_file=str(path))
    with h5py.File(path) as f:
        for child_item in f.items():
            if isinstance(child_item, h5py.Group):
                child_group_dataset = _create_hdf5_group_dataset(
                    child_item, hdf5_dataset
                )
                hdf5_dataset.children.append(child_group_dataset)
            elif isinstance(child_item, h5py.Dataset):
                child_dataset_dataset = _create_hdf5_dataset_dataset(
                    child_item, hdf5_dataset
                )
                hdf5_dataset.children.append(child_dataset_dataset)
            else:
                raise TypeError(f"Unsupported HDF5 type: {type(child_item)}")
    return hdf5_dataset


def load_hdf5_layer(layer: Layer) -> NapariLayer:
    if not isinstance(layer, HDF5Layer):
        raise TypeError(f"Not an HDF5 layer: {layer}")
    root_hdf5_dataset, hdf5_dataset_path = HDF5Dataset.get_root(layer.dataset)
    if layer.root_hdf5_dataset != root_hdf5_dataset:
        raise ValueError(f"Not part of original HDF5 dataset: {layer}")
    with h5py.File(root_hdf5_dataset.hdf5_file) as f:
        data = da.from_array(f[hdf5_dataset_path])
    napari_layer = NapariImageLayer(name=layer.name, data=data)
    return napari_layer


def _create_hdf5_group_dataset(hdf5_group: "h5py.Group", parent: Dataset) -> Dataset:
    assert isinstance(hdf5_group, h5py.Group)
    dataset = Dataset(name=hdf5_group.name, parent=parent)
    for _, child_item in hdf5_group.items():
        if isinstance(child_item, h5py.Group):
            child_group_dataset = _create_hdf5_group_dataset(child_item, dataset)
            dataset.children.append(child_group_dataset)
        elif isinstance(child_item, h5py.Dataset):
            child_dataset_dataset = _create_hdf5_dataset_dataset(child_item, dataset)
            dataset.children.append(child_dataset_dataset)
        else:
            raise TypeError(f"Unsupported HDF5 type: {type(child_item)}")
    return dataset


def _create_hdf5_dataset_dataset(
    hdf5_dataset: "h5py.Dataset", parent: Dataset
) -> Dataset:
    assert isinstance(hdf5_dataset, h5py.Dataset)
    dataset = Dataset(name=hdf5_dataset.name, parent=parent)
    root_hdf5_dataset, hdf5_path = HDF5Dataset.get_root(dataset)
    assert root_hdf5_dataset is not None
    layer = HDF5Layer(
        name=f"{Path(root_hdf5_dataset.hdf5_file).name} [{hdf5_path}]",
        dataset=dataset,
        root_hdf5_dataset=root_hdf5_dataset,
    )
    dataset.layers.append(layer)
    return dataset
