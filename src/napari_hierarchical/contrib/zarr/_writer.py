import os
from typing import Union

from napari_hierarchical.model import Group

try:
    import zarr
except ModuleNotFoundError:
    pass

PathLike = Union[str, os.PathLike]


def write_zarr(path: PathLike, group: Group) -> None:
    if group.parent is not None:
        raise ValueError(f"Not a root group: {group}")
    if not group.loaded:
        raise ValueError(f"Group is not loaded: {group}")
    z = zarr.open(store=str(path), mode="w")
    assert isinstance(z, zarr.Group)
    _write_group(group, z)


def _write_group(group: Group, zarr_group: "zarr.Group") -> None:
    for array in group.arrays:
        assert array.layer is not None
        zarr_group.create_dataset(name=array.name, data=array.layer.data)
    for child in group.children:
        g = zarr_group.create_group(name=child.name)
        _write_group(child, g)
