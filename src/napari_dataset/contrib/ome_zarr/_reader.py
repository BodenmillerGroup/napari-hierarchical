import os
from pathlib import Path
from typing import Generator, Union

import numpy as np
from napari.layers import Image as NapariImageLayer
from napari.layers import Labels as NapariLabelsLayer

from napari_dataset.model import Dataset, Layer

from .model import OMEZarrImageLayer, OMEZarrLabelsLayer

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
    dataset = Dataset(name=Path(path).name)
    for image_layer in _create_image_layers(path):
        dataset.layers.append(image_layer)
    for labels_layer in _create_labels_layers(path):
        dataset.layers.append(labels_layer)
    return dataset


def load_ome_zarr_image_layer(layer: Layer) -> None:
    if not isinstance(layer, OMEZarrImageLayer):
        raise TypeError(f"Not an OME-Zarr Image layer: {layer}")
    zarr_location = ZarrLocation(layer.ome_zarr_file)
    zarr_reader = ZarrReader(zarr_location)
    zarr_node = ZarrNode(zarr_location, zarr_reader)
    multiscales = Multiscales(zarr_node)
    data = [multiscales.array(resolution, "") for resolution in multiscales.datasets]
    if layer.channel_axis is not None and layer.channel_index is not None:
        data = [np.take(a, layer.channel_index, axis=layer.channel_axis) for a in data]
    layer.napari_layer = NapariImageLayer(name=layer.name, data=data, multiscale=True)


def load_ome_zarr_labels_layer(layer: Layer) -> None:
    if not isinstance(layer, OMEZarrLabelsLayer):
        raise TypeError(f"Not an OME-Zarr Labels layer: {layer}")
    zarr_location = ZarrLocation(layer.ome_zarr_file)
    labels_zarr_location = ZarrLocation(zarr_location.subpath("labels"))
    label_zarr_location = ZarrLocation(labels_zarr_location.subpath(layer.label_name))
    label_zarr_reader = ZarrReader(label_zarr_location)
    label_zarr_node = ZarrNode(label_zarr_location, label_zarr_reader)
    label_multiscales = Multiscales(label_zarr_node)
    data = [
        label_multiscales.array(resolution, "")
        for resolution in label_multiscales.datasets
    ]
    layer.napari_layer = NapariLabelsLayer(name=layer.name, data=data, multiscale=True)


def _create_image_layers(path: PathLike) -> Generator[OMEZarrImageLayer, None, None]:
    file_name = Path(path).name
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
        raise ValueError(f"{file_name} contains multiple channel axes")
    if channel_axis is not None:
        data = [multiscales.array(res, "") for res in multiscales.datasets]
        if len(data) == 0:
            raise ValueError(f"{file_name} does not contain any data")
        num_channels = data[0].shape[channel_axis]
        if any(a.shape[channel_axis] != num_channels for a in data):
            raise ValueError(
                f"{file_name} has resolutions with inconsistent channel numbers"
            )
        for channel_index in range(num_channels):
            image_layer = OMEZarrImageLayer(
                name=f"{file_name} [C{channel_index:02d}]",
                ome_zarr_file=str(path),
                channel_axis=channel_axis,
                channel_index=channel_index,
            )
            if channel_names is not None and len(channel_names) == num_channels:
                image_layer.groups[
                    "OME Channel"
                ] = f"[C{channel_index:02d}] channel_names[channel_index]"
            else:
                image_layer.groups[
                    "OME Channel"
                ] = f"[C{channel_index:02d}] Channel {channel_index}"
            yield image_layer
    else:
        image_layer = OMEZarrImageLayer(name=file_name)
        yield image_layer


def _create_labels_layers(path: PathLike) -> Generator[OMEZarrLabelsLayer, None, None]:
    file_name = Path(path).name
    zarr_location = ZarrLocation(str(path))
    zarr_reader = ZarrReader(zarr_location)
    for labels_zarr_node in zarr_reader():
        if (
            Labels.matches(labels_zarr_node.zarr)
            and "labels" in labels_zarr_node.zarr.root_attrs
        ):
            for label_name in labels_zarr_node.zarr.root_attrs["labels"]:
                labels_layer = OMEZarrLabelsLayer(
                    name=f"{file_name} [{label_name}]",
                    ome_zarr_file=str(path),
                    label_name=label_name,
                )
                labels_layer.groups["OME Label"] = label_name
                yield labels_layer
