import os
from typing import Dict, Generator, Optional, Union

import numpy as np
from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, Layer

from ._exceptions import BioImageOMEZarrException
from .model import OMEZarrImage, OMEZarrImageLayer, OMEZarrLabelsLayer

try:
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Label, Labels, Multiscales
    from ome_zarr.reader import Node as ZarrNode
    from ome_zarr.reader import Reader as ZarrReader
except ModuleNotFoundError:
    pass  # skipped intentionally

PathLike = Union[str, os.PathLike]


def read_ome_zarr_image(path: PathLike) -> Image:
    try:
        zarr_location = ZarrLocation(str(path))
        zarr_reader = ZarrReader(zarr_location)
        zarr_node = ZarrNode(zarr_location, zarr_reader)
        multiscales = Multiscales(zarr_node)
        label_multiscales = _try_get_label_multiscales(zarr_reader, zarr_node)
    except Exception as e:
        raise BioImageOMEZarrException(e)
    basename = multiscales.zarr.basename()
    if "axes" not in multiscales.node.metadata:
        raise BioImageOMEZarrException(f"{basename} does not contain axes metadata")
    image = OMEZarrImage(name=basename, path=str(path))
    for image_layer in _get_image_layers(image, multiscales):
        image.layers.append(image_layer)
    if label_multiscales is not None:
        for labels_layer in _try_get_labels_layers(image, label_multiscales):
            image.layers.append(labels_layer)
    return image


def _try_get_label_multiscales(
    zarr_reader: ZarrReader, zarr_node: ZarrNode
) -> Optional[Dict[str, Multiscales]]:
    labels_zarr_nodes = [
        zarr_node for zarr_node in zarr_reader() if Labels.matches(zarr_node.zarr)
    ]
    if len(labels_zarr_nodes) == 0:
        return None
    if len(labels_zarr_nodes) > 1:
        basename = zarr_node.zarr.basename()
        raise BioImageOMEZarrException(f"{basename} contains more than one labels node")
    labels = Labels(labels_zarr_nodes[0])
    if "labels" not in labels.zarr.root_attrs:
        return None
    label_multiscales = {}
    for label_name in labels.zarr.root_attrs["labels"]:
        try:
            label_zarr_location = ZarrLocation(labels.zarr.subpath(label_name))
            if not (
                Label.matches(label_zarr_location)
                and Multiscales.matches(label_zarr_location)
            ):
                continue  # TODO logging
            label_zarr_reader = ZarrReader(label_zarr_location)
            label_zarr_node = ZarrNode(label_zarr_location, label_zarr_reader)
            label_multiscales[label_name] = Multiscales(label_zarr_node)
        except Exception:
            continue  # TODO logging
    return label_multiscales


def _get_image_layers(
    image: OMEZarrImage, multiscales: Multiscales
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
        raise BioImageOMEZarrException(f"{image.name} contains multiple channel axes")
    try:
        data = [multiscales.array(res, "") for res in multiscales.datasets]
    except Exception as e:
        raise BioImageOMEZarrException(e)
    if len(data) == 0:
        raise BioImageOMEZarrException(f"{image.name} does not contain any data")
    num_channels = None
    if channel_axis is not None:
        num_channels = data[0].shape[channel_axis]
        if any(a.shape[channel_axis] != num_channels for a in data):
            raise BioImageOMEZarrException(
                f"{image.name} contains resolutions with inconsistent channel numbers"
            )
        if channel_names is not None and len(channel_names) != num_channels:
            channel_names = None  # TODO logging
    if channel_axis is not None and num_channels is not None:
        for channel_index in range(num_channels):
            channel_data = [np.take(a, channel_index, axis=channel_axis) for a in data]
            image_layer = OMEZarrImageLayer(
                name=f"{image.name} [C{channel_index}]", image=image, data=channel_data
            )
            if channel_names is not None:
                image_layer.metadata["Channel"] = channel_names[channel_index]
            else:
                image_layer.metadata["Channel"] = f"Channel {channel_index}"
            yield image_layer
    else:
        yield OMEZarrImageLayer(name=image.name, image=image, data=data)


def _try_get_labels_layers(
    image: OMEZarrImage, label_multiscales: Dict[str, Multiscales]
) -> Generator[OMEZarrLabelsLayer, None, None]:
    for label_name, multiscales in label_multiscales.items():
        try:
            data = [multiscales.array(res, "") for res in multiscales.datasets]
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
    raise BioImageOMEZarrException(f"Unsupported layer type: {type(layer)}")
