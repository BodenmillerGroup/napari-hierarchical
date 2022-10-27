import os
from pathlib import Path
from typing import Optional, Union

from napari_dataset.model import Dataset

from .model import ZarrLayer

try:
    import zarr
except ModuleNotFoundError:
    zarr = None

PathLike = Union[str, os.PathLike]


def read_zarr(path: PathLike) -> Dataset:
    zarr_file = Path(path)
    while zarr_file is not None and zarr_file.suffix != ".zarr":
        zarr_file = zarr_file.parent
    assert zarr_file is not None
    z = zarr.open(store=path, mode="r")
    name = str(Path(path).relative_to(zarr_file.parent))
    if isinstance(z, zarr.Group):
        dataset = _create_dataset_for_zarr_group(name, z)
    elif isinstance(z, zarr.Array):
        dataset = _create_dataset_for_zarr_array(name, z)
    else:
        raise TypeError(f"Unsupported zarr type: {type(z)}")
    return dataset


def _create_dataset_for_zarr_group(
    name: str, group: "zarr.Group", parent: Optional[Dataset] = None
) -> Dataset:
    dataset = Dataset(name=name, parent=parent)
    for child_group_name, child_group in group.groups():
        child_dataset = _create_dataset_for_zarr_group(
            child_group_name, child_group, parent=dataset
        )
        dataset.children.append(child_dataset)
    for child_array_name, child_array in group.arrays():
        child_dataset = _create_dataset_for_zarr_array(
            child_array_name, child_array, parent=dataset
        )
        dataset.children.append(child_dataset)
    return dataset


def _create_dataset_for_zarr_array(
    name: str, array: "zarr.Array", parent: Optional[Dataset] = None
) -> Dataset:
    dataset = Dataset(name=name, parent=parent)
    layer = ZarrLayer(
        name=f"{Path(array.path).name} [{array.name}]",
        dataset=dataset,
        zarr_file=array.path,
        path=array.name,
    )
    dataset.layers.append(layer)
    return dataset
