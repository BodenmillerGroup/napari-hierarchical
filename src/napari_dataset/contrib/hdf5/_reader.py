import os
from pathlib import Path
from typing import Optional, Union

from napari_dataset.model import Dataset, Layer

try:
    import h5py
except ModuleNotFoundError:
    h5py = None

PathLike = Union[str, os.PathLike]


def read_hdf5(path: PathLike) -> Dataset:
    with h5py.File(path) as f:
        dataset = _create_dataset_for_hdf5_group(Path(path).name, f)
    return dataset


def _create_dataset_for_hdf5_group(
    name: str, hdf5_group: "h5py.Group", parent: Optional[Dataset] = None
) -> Dataset:
    dataset = Dataset(name=name, parent=parent)
    for child_name, child_item in hdf5_group.items():
        if isinstance(child_item, h5py.Group):
            child_dataset = _create_dataset_for_hdf5_group(
                child_name, child_item, parent=dataset
            )
        elif isinstance(child_item, h5py.Dataset):
            child_dataset = _create_dataset_for_hdf5_dataset(
                child_name, child_item, parent=dataset
            )
        else:
            raise ValueError(f"Unsupported child type: {type(child_item)}")
        dataset.children.append(child_dataset)
    return dataset


def _create_dataset_for_hdf5_dataset(
    name: str, hdf5_dataset: "h5py.Dataset", parent: Optional[Dataset] = None
) -> Dataset:
    dataset = Dataset(name=name, parent=parent)
    layer = Layer(
        name=f"{Path(hdf5_dataset.file.filename).name} [{hdf5_dataset.name}]",
        dataset=dataset,
        hdf5_file=hdf5_dataset.file.filename,
        path=hdf5_dataset.name,
    )
    dataset.layers.append(layer)
    return dataset
