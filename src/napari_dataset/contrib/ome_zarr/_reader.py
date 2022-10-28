import os
from pathlib import Path
from typing import Generator, Union

import numpy as np
from napari.layers import Image as NapariImageLayer
from napari.layers import Labels as NapariLabelsLayer
from napari.layers import Layer as NapariLayer

from napari_dataset.model import Dataset, Layer

from .model import OMEZarrDataset, OMEZarrImageLayer, OMEZarrLabelsLayer

try:
    import ome_zarr
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Labels, Multiscales
    from ome_zarr.reader import Node as ZarrNode
    from ome_zarr.reader import Reader as ZarrReader
except ModuleNotFoundError:
    ome_zarr = None

PathLike = Union[str, os.PathLike]


def read_ome_zarr_dataset(path: PathLike) -> Dataset:
    ome_zarr_dataset = OMEZarrDataset(name=Path(path).name, ome_zarr_file=str(path))
    for ome_zarr_image_layer in _create_ome_zarr_image_layers(path, ome_zarr_dataset):
        ome_zarr_dataset.layers.append(ome_zarr_image_layer)
    for ome_zarr_labels_layer in _create_ome_zarr_labels_layers(path, ome_zarr_dataset):
        ome_zarr_dataset.layers.append(ome_zarr_labels_layer)
    return ome_zarr_dataset


def load_ome_zarr_image_layer(layer: Layer) -> NapariLayer:
    if not isinstance(layer, OMEZarrImageLayer):
        raise TypeError(f"Not an OME-Zarr Image layer: {layer}")
    ome_zarr_dataset = layer.ome_zarr_dataset
    if layer.dataset != ome_zarr_dataset:
        raise ValueError(f"Not part of original OME-Zarr dataset: {layer}")
    zarr_location = ZarrLocation(ome_zarr_dataset.ome_zarr_file)
    zarr_reader = ZarrReader(zarr_location)
    zarr_node = ZarrNode(zarr_location, zarr_reader)
    multiscales = Multiscales(zarr_node)
    data = [multiscales.array(resolution, "") for resolution in multiscales.datasets]
    if layer.channel_axis is not None and layer.channel_index is not None:
        data = [np.take(a, layer.channel_index, axis=layer.channel_axis) for a in data]
    napari_layer = NapariImageLayer(name=layer.name, data=data, multiscale=True)
    return napari_layer


def load_ome_zarr_labels_layer(layer: Layer) -> NapariLayer:
    if not isinstance(layer, OMEZarrLabelsLayer):
        raise TypeError(f"Not an OME-Zarr Labels layer: {layer}")
    ome_zarr_dataset = layer.ome_zarr_dataset
    if layer.dataset != ome_zarr_dataset:
        raise ValueError(f"Not part of original OME-Zarr dataset: {layer}")
    zarr_location = ZarrLocation(ome_zarr_dataset.ome_zarr_file)
    labels_zarr_location = ZarrLocation(zarr_location.subpath("labels"))
    label_zarr_location = ZarrLocation(labels_zarr_location.subpath(layer.label_name))
    label_zarr_reader = ZarrReader(label_zarr_location)
    label_zarr_node = ZarrNode(label_zarr_location, label_zarr_reader)
    label_multiscales = Multiscales(label_zarr_node)
    data = [
        label_multiscales.array(resolution, "")
        for resolution in label_multiscales.datasets
    ]
    napari_layer = NapariLabelsLayer(name=layer.name, data=data, multiscale=True)
    return napari_layer


def _create_ome_zarr_image_layers(
    path: PathLike, ome_zarr_dataset: OMEZarrDataset
) -> Generator[OMEZarrImageLayer, None, None]:
    zarr_location = ZarrLocation(str(path))
    zarr_reader = ZarrReader(zarr_location)
    zarr_node = ZarrNode(zarr_location, zarr_reader)
    multiscales = Multiscales(zarr_node)
    channel_axes = [
        axis
        for axis, axis_dict in enumerate(multiscales.node.metadata["axes"])
        if axis_dict.get("type") == "channel"
    ]
    if len(channel_axes) == 0:
        channel_axis = None
        channel_names = None
    elif len(channel_axes) == 1:
        channel_axis = channel_axes[0]
        channel_names = multiscales.node.metadata.get("name")
    else:
        raise ValueError(f"{ome_zarr_dataset} contains multiple channel axes")
    if channel_axis is not None:
        data = [multiscales.array(res, "") for res in multiscales.datasets]
        if len(data) == 0:
            raise ValueError(f"{ome_zarr_dataset} does not contain any data")
        num_channels = data[0].shape[channel_axis]
        if any(a.shape[channel_axis] != num_channels for a in data):
            raise ValueError(
                f"{ome_zarr_dataset} has resolutions with inconsistent channel numbers"
            )
        for channel_index in range(num_channels):
            ome_zarr_image_layer = OMEZarrImageLayer(
                name=f"{ome_zarr_dataset.name} [C{channel_index:02d}]",
                dataset=ome_zarr_dataset,
                ome_zarr_dataset=ome_zarr_dataset,
                channel_axis=channel_axis,
                channel_index=channel_index,
            )
            if channel_names is not None and len(channel_names) == num_channels:
                ome_zarr_image_layer.groups[
                    "Channel"
                ] = f"[C{channel_index:02d}] channel_names[channel_index]"
            else:
                ome_zarr_image_layer.groups[
                    "Channel"
                ] = f"[C{channel_index:02d}] Channel {channel_index}"
            yield ome_zarr_image_layer
    else:
        ome_zarr_image_layer = OMEZarrImageLayer(
            name=ome_zarr_dataset.name,
            dataset=ome_zarr_dataset,
            ome_zarr_dataset=ome_zarr_dataset,
        )
        yield ome_zarr_image_layer


def _create_ome_zarr_labels_layers(
    path: PathLike, ome_zarr_dataset: OMEZarrDataset
) -> Generator[OMEZarrLabelsLayer, None, None]:
    zarr_location = ZarrLocation(str(path))
    zarr_reader = ZarrReader(zarr_location)
    for labels_zarr_node in zarr_reader():
        if (
            Labels.matches(labels_zarr_node.zarr)
            and "labels" in labels_zarr_node.zarr.root_attrs
        ):
            for label_name in labels_zarr_node.zarr.root_attrs["labels"]:
                ome_zarr_labels_layer = OMEZarrLabelsLayer(
                    name=f"{ome_zarr_dataset.name} [{label_name}]",
                    dataset=ome_zarr_dataset,
                    ome_zarr_dataset=ome_zarr_dataset,
                    label_name=label_name,
                )
                ome_zarr_labels_layer.groups["Label"] = label_name
                yield ome_zarr_labels_layer
