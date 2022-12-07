import os
from pathlib import Path
from typing import Optional, Sequence, Union

from napari.layers import Image

from napari_hierarchical.model import Array, Group

try:
    import dask.array as da
    import h5py
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def read_hdf5(path: PathLike) -> Group:
    with h5py.File(path) as f:
        group = _create_group(str(path), [], f, name=Path(path).name)
    group.commit()
    return group


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
        else:
            raise NotImplementedError()
    return group


def _create_array(
    hdf5_file: str, hdf5_names: Sequence[str], hdf5_dataset: "h5py.Dataset"
) -> Array:
    hdf5_path = "/".join(hdf5_names)
    name = f"{Path(hdf5_file).name} [/{hdf5_path}]"
    layer = Image(name=name, data=da.from_array(hdf5_dataset))
    array = Array(name=name, loaded_layer=layer)
    if len(hdf5_names) > 0:
        array.flat_grouping_groups["Path"] = (
            "/*" * (len(hdf5_names) - 1) + "/" + hdf5_names[-1]
        )
    else:
        array.flat_grouping_groups["Path"] = "/"
    return array
