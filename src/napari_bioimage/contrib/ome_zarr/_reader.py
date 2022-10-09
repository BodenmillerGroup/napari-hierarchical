import os
from typing import Dict, Generator, Union

import numpy as np
from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, Layer

from .model import OMEZarrImageLayer, OMEZarrLabelsLayer

try:
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Label, Labels, Multiscales
    from ome_zarr.reader import Node as ZarrNode
    from ome_zarr.reader import Reader as ZarrReader
except ModuleNotFoundError:
    pass  # skipped intentionally

PathLike = Union[str, os.PathLike]


def read_ome_zarr_image(path: PathLike) -> Image:
    zarr_location = ZarrLocation(str(path))
    zarr_reader = ZarrReader(zarr_location)
    image = Image(name=zarr_location.basename())
    zarr_node = ZarrNode(zarr_location, zarr_reader)
    multiscales = Multiscales(zarr_node)
    for image_layer in _get_image_layers(image, multiscales):
        image.layers.append(image_layer)
    label_multiscales = _get_label_multiscales(zarr_reader)
    for labels_layer in _get_labels_layers(image, label_multiscales):
        image.layers.append(labels_layer)
    return image


def _get_label_multiscales(zarr_reader: "ZarrReader") -> Dict[str, "Multiscales"]:
    label_multiscales = {}
    for labels_zarr_node in zarr_reader():
        if (
            Labels.matches(labels_zarr_node.zarr)
            and "labels" in labels_zarr_node.zarr.root_attrs
        ):
            for label_name in labels_zarr_node.zarr.root_attrs["labels"]:
                label_zarr_location = ZarrLocation(
                    labels_zarr_node.zarr.subpath(label_name)
                )
                if (
                    label_zarr_location.exists()
                    and Label.matches(label_zarr_location)
                    and Multiscales.matches(label_zarr_location)
                ):
                    label_zarr_reader = ZarrReader(label_zarr_location)
                    label_zarr_node = ZarrNode(label_zarr_location, label_zarr_reader)
                    label_multiscales[label_name] = Multiscales(label_zarr_node)
    return label_multiscales


def _get_image_layers(
    image: Image, multiscales: "Multiscales"
) -> Generator[OMEZarrImageLayer, None, None]:
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
        raise ValueError(f"{image.name} contains multiple channel axes")
    data = [multiscales.array(res, "") for res in multiscales.datasets]
    if len(data) == 0:
        raise ValueError(f"{image.name} does not contain any data")
    if channel_axis is not None:
        num_channels = data[0].shape[channel_axis]
        if any(a.shape[channel_axis] != num_channels for a in data):
            raise ValueError(
                f"{image.name} contains resolutions with inconsistent channel numbers"
            )
        for channel_index in range(num_channels):
            channel_data = [np.take(a, channel_index, axis=channel_axis) for a in data]
            image_layer = OMEZarrImageLayer(
                name=f"{image.name} [C{channel_index}]", image=image, data=channel_data
            )
            if channel_names is not None and len(channel_names) == num_channels:
                image_layer.metadata["Channel"] = channel_names[channel_index]
            else:
                image_layer.metadata["Channel"] = f"Channel {channel_index}"
            yield image_layer
    else:
        yield OMEZarrImageLayer(name=image.name, image=image, data=data)


def _get_labels_layers(
    image: Image, label_multiscales: Dict[str, "Multiscales"]
) -> Generator[OMEZarrLabelsLayer, None, None]:
    for label_name, multiscales in label_multiscales.items():
        try:
            data = [
                multiscales.array(resolution, "") for resolution in multiscales.datasets
            ]  # TODO version
        except Exception:
            continue  # TODO logging
        if len(data) == 0:
            continue  # TODO logging
        labels_layer = OMEZarrLabelsLayer(
            name=f"{image.name} [{label_name}]", image=image, data=data
        )
        labels_layer["Label"] = label_name
        yield labels_layer


def load_ome_zarr_layer(layer: Layer, viewer: Viewer) -> NapariLayer:
    if isinstance(layer, OMEZarrImageLayer):
        return viewer.add_image(data=layer.data, name=layer.name, multiscale=True)
    if isinstance(layer, OMEZarrLabelsLayer):
        return viewer.add_labels(data=layer.data, name=layer.name, multiscale=True)
    raise TypeError(f"Unsupported layer type: {type(layer)}")
