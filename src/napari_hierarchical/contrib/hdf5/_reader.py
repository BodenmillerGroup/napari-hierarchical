import os
from pathlib import Path
from typing import Optional, Sequence, Union

from napari.layers import Image

from napari_hierarchical.model import Group

from .model import HDF5Array

try:
    import dask.array as da
    import h5py
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def read_hdf5(path: PathLike) -> Group:
    with h5py.File(path) as f:
        return _create_group(str(path), [], f, name=Path(path).name)


def _create_group(
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
            child = _create_group(hdf5_file, [*hdf5_names, hdf5_name], hdf5_item)
            group.children.append(child)
        elif isinstance(hdf5_item, h5py.Dataset):
            array = _create_array(hdf5_file, [*hdf5_names, hdf5_name], hdf5_item)
            group.arrays.append(array)
    return group


def _create_array(
    hdf5_file: str,
    hdf5_names: Sequence[str],
    hdf5_dataset: "h5py.Dataset",
    name: Optional[str] = None,
) -> HDF5Array:
    hdf5_path = "/".join(hdf5_names)
    if name is None:
        name = f"{Path(hdf5_file).name} [/{hdf5_path}]"
    layer = Image(name=name, data=da.from_array(hdf5_dataset))
    array = HDF5Array(
        name=name, loaded_layer=layer, hdf5_file=hdf5_file, hdf5_path=hdf5_path
    )
    if len(hdf5_names) > 0:
        array.flat_grouping_groups["Path"] = (
            "/*" * (len(hdf5_names) - 1) + "/" + hdf5_names[-1]
        )
    else:
        array.flat_grouping_groups["Path"] = "/"
    return array
