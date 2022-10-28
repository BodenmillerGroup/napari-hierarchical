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
    zarr_dataset = ZarrDataset(name=Path(path).name, zarr_file=str(path))
    z = zarr.open(store=str(path), mode="r")
    if isinstance(z, zarr.Group):
        for _, child_group in z.groups():
            child_group_dataset = _create_zarr_group_dataset(child_group, zarr_dataset)
            zarr_dataset.children.append(child_group_dataset)
        for _, child_array in z.arrays():
            child_array_dataset = _create_zarr_array_dataset(child_array, zarr_dataset)
            zarr_dataset.children.append(child_array_dataset)
    elif isinstance(z, zarr.Array):
        layer = Layer(name=zarr_dataset.name, dataset=zarr_dataset)
        zarr_dataset.layers.append(layer)
    else:
        raise TypeError(f"Unsupported Zarr type: {type(z)}")
    return zarr_dataset


def load_zarr_layer(layer: Layer) -> NapariLayer:
    if not isinstance(layer, ZarrLayer):
        raise TypeError(f"Not a Zarr layer: {layer}")
    root_zarr_dataset, zarr_path = ZarrDataset.get_root(layer.dataset)
    if layer.root_zarr_dataset != root_zarr_dataset:
        raise ValueError(f"Not part of original Zarr dataset: {layer}")
    z = zarr.open(store=root_zarr_dataset.zarr_file, mode="r")
    data = da.from_zarr(z[zarr_path])
    napari_layer = NapariImageLayer(name=layer.name, data=data)
    return napari_layer


def _create_zarr_group_dataset(zarr_group: "zarr.Group", parent: Dataset) -> Dataset:
    assert isinstance(zarr_group, zarr.Group)
    dataset = Dataset(name=zarr_group.name, parent=parent)
    for _, child_group in zarr_group.groups():
        child_group_dataset = _create_zarr_group_dataset(child_group, dataset)
        dataset.children.append(child_group_dataset)
    for _, child_array in zarr_group.arrays():
        child_array_dataset = _create_zarr_array_dataset(child_array, dataset)
        dataset.children.append(child_array_dataset)
    return dataset


def _create_zarr_array_dataset(zarr_array: "zarr.Array", parent: Dataset) -> Dataset:
    assert isinstance(zarr_array, zarr.Array)
    dataset = Dataset(name=zarr_array.name, parent=parent)
    root_zarr_dataset, zarr_path = ZarrDataset.get_root(dataset)
    assert root_zarr_dataset is not None
    layer = ZarrLayer(
        name=f"{Path(root_zarr_dataset.zarr_file).name} [{zarr_path}]",
        dataset=dataset,
        root_zarr_dataset=root_zarr_dataset,
    )
    dataset.layers.append(layer)
    return dataset
