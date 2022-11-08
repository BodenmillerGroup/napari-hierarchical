import os
from pathlib import Path
from typing import Optional, Sequence, Union

from napari.layers import Image as NapariImageLayer

from napari_dataset.model import Dataset

from .model import ZarrLayer

try:
    import dask.array as da
    import zarr
except ModuleNotFoundError:
    da = None
    zarr = None

PathLike = Union[str, os.PathLike]


def read_zarr_dataset(path: PathLike) -> Dataset:
    z = zarr.open(store=str(path), mode="r")
    if isinstance(z, zarr.Array):
        dataset = Dataset(name=Path(path).name)
        layer = _create_layer(str(path), [], z)
        dataset.layers.append(layer)
        return dataset
    if isinstance(z, zarr.Group):
        return _create_dataset(str(path), [], z, name=Path(path).name)
    raise TypeError(f"Unsupported Zarr type: {type(z)}")


def _create_dataset(
    zarr_file: str,
    zarr_names: Sequence[str],
    zarr_group: "zarr.Group",
    name: Optional[str] = None,
) -> Dataset:
    assert isinstance(zarr_group, zarr.Group)
    if name is None:
        name = zarr_group.basename
    dataset = Dataset(name=name)
    for zarr_name, zarr_child in zarr_group.groups():
        child = _create_dataset(zarr_file, [*zarr_names, zarr_name], zarr_child)
        dataset.children.append(child)
    for zarr_name, zarr_array in zarr_group.arrays():
        layer = _create_layer(zarr_file, [*zarr_names, zarr_name], zarr_array)
        dataset.layers.append(layer)
    return dataset


def _create_layer(
    zarr_file: str,
    zarr_names: Sequence[str],
    zarr_array: "zarr.Array",
    name: Optional[str] = None,
) -> ZarrLayer:
    assert isinstance(zarr_array, zarr.Array)
    zarr_path = "/".join(zarr_names)
    if name is None:
        name = f"{Path(zarr_file).name} [/{zarr_path}]"
    napari_layer_data = da.from_zarr(zarr_array)
    napari_layer = NapariImageLayer(name=name, data=napari_layer_data)
    layer = ZarrLayer(
        name=name,
        loaded_napari_layer=napari_layer,
        zarr_file=zarr_file,
        zarr_path=zarr_path,
    )
    if len(zarr_names) > 0:
        layer.groups["Path"] = "/*" * (len(zarr_names) - 1) + "/" + zarr_names[-1]
    else:
        layer.groups["Path"] = "/"
    return layer
