import os
from pathlib import Path
from typing import Optional, Sequence, Union

from napari.layers import Image

from napari_hierarchical.model import Group

from .model import ZarrArray

try:
    import dask.array as da
    import zarr
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def read_zarr(path: PathLike) -> Group:
    z = zarr.open(store=str(path), mode="r")
    if isinstance(z, zarr.Array):
        group = Group(name=Path(path).name)
        array = _create_array(str(path), [], z)
        group.arrays.append(array)
    elif isinstance(z, zarr.Group):
        group = _create_group(str(path), [], z, name=Path(path).name)
    else:
        raise TypeError(f"Unsupported Zarr type: {type(z)}")
    group.commit()
    return group


def _create_group(
    zarr_file: str,
    zarr_names: Sequence[str],
    zarr_group: "zarr.Group",
    name: Optional[str] = None,
) -> Group:
    if name is None:
        name = zarr_group.basename
    group = Group(name=name)
    for zarr_name, zarr_child in zarr_group.groups():
        child = _create_group(zarr_file, [*zarr_names, zarr_name], zarr_child)
        group.children.append(child)
    for zarr_name, zarr_array in zarr_group.arrays():
        array = _create_array(zarr_file, [*zarr_names, zarr_name], zarr_array)
        group.arrays.append(array)
    return group


def _create_array(
    zarr_file: str,
    zarr_names: Sequence[str],
    zarr_array: "zarr.Array",
    name: Optional[str] = None,
) -> ZarrArray:
    zarr_path = "/".join(zarr_names)
    if name is None:
        name = f"{Path(zarr_file).name} [/{zarr_path}]"
    layer = Image(name=name, data=da.from_zarr(zarr_array))
    array = ZarrArray(
        name=name,
        loaded_layer=layer,
        zarr_file=zarr_file,
        zarr_path=zarr_path,
    )
    if len(zarr_names) > 0:
        array.flat_grouping_groups["Path"] = (
            "/*" * (len(zarr_names) - 1) + "/" + zarr_names[-1]
        )
    else:
        array.flat_grouping_groups["Path"] = "/"
    return array
