import os
from pathlib import Path
from typing import Sequence, Union

from napari.layers import Image as NapariImageLayer

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
    root_dataset = HDF5Dataset(name=Path(path).name, hdf5_file=str(path))
    with h5py.File(path) as f:
        for child_hdf5_item_name, child_hdf5_item in f.items():
            if isinstance(child_hdf5_item, h5py.Group):
                child_group_dataset = _create_hdf5_group_dataset(
                    root_dataset, child_hdf5_item, [child_hdf5_item_name]
                )
                root_dataset.children.append(child_group_dataset)
            elif isinstance(child_hdf5_item, h5py.Dataset):
                child_dataset_dataset = _create_hdf5_dataset_dataset(
                    root_dataset, child_hdf5_item, [child_hdf5_item_name]
                )
                root_dataset.children.append(child_dataset_dataset)
            else:
                raise TypeError(f"Unsupported HDF5 type: {type(child_hdf5_item)}")
    return root_dataset


def load_hdf5_layer(layer: Layer) -> None:
    if not isinstance(layer, HDF5Layer):
        raise TypeError(f"Not an HDF5 layer: {layer}")
    dataset = layer.get_parent()
    assert dataset is not None
    root_hdf5_dataset, hdf5_names = dataset.get_root()
    if root_hdf5_dataset != layer.root_hdf5_dataset:
        raise ValueError(f"Not part of original HDF5 dataset: {layer}")
    assert isinstance(root_hdf5_dataset, HDF5Dataset)
    with h5py.File(root_hdf5_dataset.hdf5_file) as f:
        data = da.from_array(f["/".join(hdf5_names)])
    layer.napari_layer = NapariImageLayer(name=layer.name, data=data)


def _create_hdf5_group_dataset(
    root_dataset: HDF5Dataset, hdf5_group: "h5py.Group", hdf5_names: Sequence[str]
) -> Dataset:
    assert isinstance(hdf5_group, h5py.Group)
    dataset = Dataset(name=hdf5_group.name)
    for child_hdf5_item_name, child_hdf5_item in hdf5_group.items():
        if isinstance(child_hdf5_item, h5py.Group):
            child_group_dataset = _create_hdf5_group_dataset(
                root_dataset, child_hdf5_item, [*hdf5_names, child_hdf5_item_name]
            )
            dataset.children.append(child_group_dataset)
        elif isinstance(child_hdf5_item, h5py.Dataset):
            child_dataset_dataset = _create_hdf5_dataset_dataset(
                root_dataset, child_hdf5_item, [*hdf5_names, child_hdf5_item_name]
            )
            dataset.children.append(child_dataset_dataset)
        else:
            raise TypeError(f"Unsupported HDF5 type: {type(child_hdf5_item)}")
    return dataset


def _create_hdf5_dataset_dataset(
    root_dataset: HDF5Dataset, hdf5_dataset: "h5py.Dataset", hdf5_names: Sequence[str]
) -> Dataset:
    assert isinstance(hdf5_dataset, h5py.Dataset)
    dataset = Dataset(name=hdf5_dataset.name)
    layer = HDF5Layer(
        name=f"{Path(root_dataset.hdf5_file).name} [{'/'.join(hdf5_names)}]",
        dataset=dataset,
        root_hdf5_dataset=root_dataset,
    )
    dataset.layers.append(layer)
    return dataset
