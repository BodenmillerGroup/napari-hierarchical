import os
from pathlib import Path
from typing import Union

from napari.layers import Image as NapariImageLayer
from napari.layers import Layer as NapariLayer

from napari_dataset.model import Dataset, Layer

from .model import ZarrDataset, ZarrLayer

try:
    import dask.array as da
    import zarr
except ModuleNotFoundError:
    da = None
    zarr = None

PathLike = Union[str, os.PathLike]


def read_zarr_dataset(path: PathLike) -> Dataset:
    root_dataset = ZarrDataset(name=Path(path).name, zarr_file=str(path))
    z = zarr.open(store=str(path), mode="r")
    if isinstance(z, zarr.Group):
        for _, child_zarr_group in z.groups():
            child_group_dataset = _create_zarr_group_dataset(
                root_dataset, child_zarr_group
            )
            root_dataset.children.append(child_group_dataset)
        for _, child_zarr_array in z.arrays():
            child_array_dataset = _create_zarr_array_dataset(
                root_dataset, child_zarr_array
            )
            root_dataset.children.append(child_array_dataset)
    elif isinstance(z, zarr.Array):
        layer = Layer(name=root_dataset.name, dataset=root_dataset)
        root_dataset.layers.append(layer)
    else:
        raise TypeError(f"Unsupported Zarr type: {type(z)}")
    return root_dataset


def load_zarr_layer(layer: Layer) -> NapariLayer:
    if not isinstance(layer, ZarrLayer):
        raise TypeError(f"Not a Zarr layer: {layer}")
    dataset = layer.get_parent()
    assert dataset is not None
    root_zarr_dataset, zarr_names = dataset.get_root()
    if root_zarr_dataset != layer._root_zarr_dataset:
        raise ValueError(f"Not part of original Zarr dataset: {layer}")
    assert isinstance(root_zarr_dataset, ZarrDataset)
    z = zarr.open(store=root_zarr_dataset.zarr_file, mode="r")
    data = da.from_zarr(z["/".join(zarr_names)])
    napari_layer = NapariImageLayer(name=layer.name, data=data)
    return napari_layer


def _create_zarr_group_dataset(
    root_dataset: ZarrDataset, zarr_group: "zarr.Group"
) -> Dataset:
    assert isinstance(zarr_group, zarr.Group)
    dataset = Dataset(name=zarr_group.basename)
    for _, child_zarr_group in zarr_group.groups():
        child_group_dataset = _create_zarr_group_dataset(root_dataset, child_zarr_group)
        dataset.children.append(child_group_dataset)
    for _, child_zarr_array in zarr_group.arrays():
        child_array_dataset = _create_zarr_array_dataset(root_dataset, child_zarr_array)
        dataset.children.append(child_array_dataset)
    return dataset


def _create_zarr_array_dataset(
    root_dataset: ZarrDataset, zarr_array: "zarr.Array"
) -> Dataset:
    assert isinstance(zarr_array, zarr.Array)
    dataset = Dataset(name=zarr_array.basename)
    layer = ZarrLayer(
        name=f"{Path(root_dataset.zarr_file).name} [{zarr_array.name}]",
        dataset=dataset,
        root_zarr_dataset=root_dataset,
    )
    dataset.layers.append(layer)
    return dataset
