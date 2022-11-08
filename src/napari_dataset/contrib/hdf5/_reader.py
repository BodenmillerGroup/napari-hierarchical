import os
from pathlib import Path
from typing import Optional, Sequence, Union

from napari.layers import Image as NapariImageLayer

from napari_dataset.model import Dataset

from .model import HDF5Layer

try:
    import dask.array as da
    import h5py
except ModuleNotFoundError:
    da = None
    h5py = None

PathLike = Union[str, os.PathLike]


def read_hdf5_dataset(path: PathLike) -> Dataset:
    with h5py.File(path) as f:
        return _create_dataset(str(path), [], f, name=Path(path).name)


def _create_dataset(
    hdf5_file: str,
    hdf5_names: Sequence[str],
    hdf5_group: "h5py.Group",
    name: Optional[str] = None,
) -> Dataset:
    assert isinstance(hdf5_group, h5py.Group)
    if name is None:
        name = Path(hdf5_group.name).name
    dataset = Dataset(name=name)
    for hdf5_name, hdf5_item in hdf5_group.items():
        if isinstance(hdf5_item, h5py.Group):
            child = _create_dataset(hdf5_file, [*hdf5_names, hdf5_name], hdf5_item)
            dataset.children.append(child)
        elif isinstance(hdf5_item, h5py.Dataset):
            layer = _create_layer(hdf5_file, [*hdf5_names, hdf5_name], hdf5_item)
            dataset.layers.append(layer)
    return dataset


def _create_layer(
    hdf5_file: str,
    hdf5_names: Sequence[str],
    hdf5_dataset: "h5py.Dataset",
    name: Optional[str] = None,
) -> HDF5Layer:
    assert isinstance(hdf5_dataset, h5py.Dataset)
    hdf5_path = "/".join(hdf5_names)
    if name is None:
        name = f"{Path(hdf5_file).name} [/{hdf5_path}]"
    layer = HDF5Layer(
        name=name,
        loaded_napari_layer=NapariImageLayer(
            name=name, data=da.from_array(hdf5_dataset)
        ),
        hdf5_file=hdf5_file,
        hdf5_path=hdf5_path,
    )
    if len(hdf5_names) > 0:
        layer.groups["Path"] = "/*" * (len(hdf5_names) - 1) + "/" + hdf5_names[-1]
    else:
        layer.groups["Path"] = "/"
    return layer
