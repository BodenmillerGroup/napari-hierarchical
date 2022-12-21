import os
from pathlib import Path
from typing import Optional, Sequence, Union

from napari.layers import Image

from napari_hierarchical.model import Array, Group

from .model import HDF5Array

try:
    import dask.array as da
    import h5py
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def read_hdf5_group(path: PathLike) -> Group:
    with h5py.File(path) as f:
        group = _read_hdf5_group(str(path), [], f, name=Path(path).name)
    group.commit()
    return group


def load_hdf5_array(array: Array) -> None:
    if not isinstance(array, HDF5Array):
        raise ValueError(f"Not an HDF5 array: {array}")
    with h5py.File(array.hdf5_file) as f:
        data = da.from_array(f[array.hdf5_path][:])
    array.layer = Image(name=array.name, data=data)


def _read_hdf5_group(
    hdf5_file: str,
    hdf5_names: Sequence[str],
    hdf5_group: "h5py.Group",
    name: Optional[str] = None,
) -> Group:
    if name is None:
        name = Path(hdf5_group.name).name
    group = Group(name=name)
    for hdf5_name, hdf5_item in hdf5_group.items():
        if isinstance(hdf5_item, h5py.Group):
            child = _read_hdf5_group(hdf5_file, [*hdf5_names, hdf5_name], hdf5_item)
            group.children.append(child)
        elif isinstance(hdf5_item, h5py.Dataset):
            array = _read_hdf5_array(hdf5_file, [*hdf5_names, hdf5_name], hdf5_item)
            group.arrays.append(array)
        else:
            raise NotImplementedError()
    return group


def _read_hdf5_array(
    hdf5_file: str, hdf5_names: Sequence[str], hdf5_dataset: "h5py.Dataset"
) -> HDF5Array:
    assert len(hdf5_names) > 0
    hdf5_path = "/".join(hdf5_names)
    name = f"{Path(hdf5_file).name}/{hdf5_path}"
    array = HDF5Array(name=name, hdf5_file=hdf5_file, hdf5_path=hdf5_path)
    array.flat_grouping_groups["Path"] = (
        "/*" * (len(hdf5_names) - 1) + "/" + hdf5_names[-1]
    )
    return array
