import os
from pathlib import Path
from typing import Union

from napari_hierarchical.model import Array, Group

from .model import HDF5Array

try:
    import h5py
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def write_hdf5_group(path: PathLike, group: Group) -> None:
    if group.parent is not None:
        raise ValueError(f"Not a root group: {group}")
    if not group.loaded:
        raise ValueError(f"Group is not loaded: {group}")
    with h5py.File(path, mode="w") as f:
        _write_hdf5_group(group, f)


def save_hdf5_array(array: Array) -> None:
    if not isinstance(array, HDF5Array):
        raise ValueError(f"Not an HDF5 array: {array}")
    if not array.loaded:
        raise ValueError(f"Array is not loaded: {array}")
    assert array.layer is not None
    with h5py.File(array.hdf5_file, mode="r+") as f:
        f[array.hdf5_path][:] = array.layer.data


def _write_hdf5_group(group: Group, hdf5_group: "h5py.Group") -> None:
    for array in group.arrays:
        assert array.layer is not None
        hdf5_group.create_dataset(name=Path(array.name).name, data=array.layer.data)
    for child in group.children:
        g = hdf5_group.create_group(name=child.name)
        _write_hdf5_group(child, g)
