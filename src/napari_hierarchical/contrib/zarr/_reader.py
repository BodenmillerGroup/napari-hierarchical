import os
from pathlib import Path
from typing import Optional, Sequence, Union

from napari.layers import Image

from napari_hierarchical.model import Array, Group

from .model import ZarrArray

try:
    import dask.array as da
    import zarr
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def read_zarr_group(path: PathLike) -> Group:
    z = zarr.open(store=str(path), mode="r")
    if isinstance(z, zarr.Array):
        group = Group(name=Path(path).name)
        array = _read_zarr_array(str(path), [], z)
        group.arrays.append(array)
    elif isinstance(z, zarr.Group):
        group = _read_zarr_group(str(path), [], z, name=Path(path).name)
    else:
        raise TypeError(f"Unsupported Zarr type: {type(z)}")
    group.commit()
    return group


def load_zarr_array(array: Array) -> None:
    if not isinstance(array, ZarrArray):
        raise ValueError(f"Not a Zarr array: {array}")
    z = zarr.open(store=array.zarr_file, mode="r")
    data = da.from_array(z[array.zarr_path][:])
    array.layer = Image(name=array.name, data=data)


def _read_zarr_group(
    zarr_file: str,
    zarr_names: Sequence[str],
    zarr_group: "zarr.Group",
    name: Optional[str] = None,
) -> Group:
    if name is None:
        name = zarr_group.basename
    group = Group(name=name)
    for zarr_name, zarr_child in zarr_group.groups():
        child = _read_zarr_group(zarr_file, [*zarr_names, zarr_name], zarr_child)
        group.children.append(child)
    for zarr_name, zarr_array in zarr_group.arrays():
        array = _read_zarr_array(zarr_file, [*zarr_names, zarr_name], zarr_array)
        group.arrays.append(array)
    return group


def _read_zarr_array(
    zarr_file: str, zarr_names: Sequence[str], zarr_array: "zarr.Array"
) -> ZarrArray:
    zarr_path = "/".join(zarr_names)
    name = Path(zarr_file).name
    if len(zarr_names) > 0:
        name += f"/{zarr_path}"
    array = ZarrArray(name=name, zarr_file=zarr_file, zarr_path=zarr_path)
    if len(zarr_names) > 0:
        array.flat_grouping_groups["Path"] = (
            "/*" * (len(zarr_names) - 1) + "/" + zarr_names[-1]
        )
    else:
        array.flat_grouping_groups["Path"] = "/"
    return array
