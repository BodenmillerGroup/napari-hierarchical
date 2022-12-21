import os
from pathlib import Path
from typing import Union

import numpy as np

from napari_hierarchical.model import Array, Group

from .model import ZarrArray

try:
    import zarr
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def write_zarr_group(path: PathLike, group: Group) -> None:
    if group.parent is not None:
        raise ValueError(f"Not a root group: {group}")
    if not group.loaded:
        raise ValueError(f"Group is not loaded: {group}")
    z = zarr.open(store=str(path), mode="w")
    assert isinstance(z, zarr.Group)
    _write_zarr_group(group, z)


def save_zarr_array(array: Array) -> None:
    if not isinstance(array, ZarrArray):
        raise ValueError(f"Not a Zarr array: {array}")
    if not array.loaded:
        raise ValueError(f"Array is not loaded: {array}")
    assert array.layer is not None
    z = zarr.open(store=array.zarr_file, mode="r+")
    z[array.zarr_path][:] = array.layer.data


def _write_zarr_group(group: Group, zarr_group: "zarr.Group") -> None:
    for array in group.arrays:
        assert array.layer is not None
        data = np.asarray(array.layer.data)
        zarr_group.create_dataset(name=Path(array.name).name, data=data)
    for child in group.children:
        g = zarr_group.create_group(name=child.name)
        _write_zarr_group(child, g)
