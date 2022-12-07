import os
from typing import Union

from napari_hierarchical.model import Group

try:
    import h5py
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def write_hdf5(path: PathLike, group: Group) -> None:
    if group.parent is not None:
        raise ValueError(f"Not a root group: {group}")
    if not group.loaded:
        raise ValueError(f"Group is not loaded: {group}")
    with h5py.File(path, mode="w") as f:
        _write_group(group, f)


def _write_group(group: Group, hdf5_group: "h5py.Group") -> None:
    for array in group.arrays:
        assert array.layer is not None
        hdf5_group.create_dataset(name=array.name, data=array.layer.data)
    for child in group.children:
        g = hdf5_group.create_group(name=child.name)
        _write_group(child, g)
