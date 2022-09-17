import os
from pathlib import Path
from typing import Generator, List, Union

import dask.array as da
import numpy as np
from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer
from ome_zarr.io import ZarrLocation
from ome_zarr.reader import Label, Multiscales
from ome_zarr.reader import Reader as ZarrReader

from napari_bioimage.model import Image, Layer

from .model import ZarrImage, ZarrImageLayer, ZarrLabelsLayer

PathLike = Union[str, os.PathLike]


class ZarrReaderError(Exception):
    pass


def read_zarr_image(path: PathLike) -> Image:
    if not isinstance(path, str) and not isinstance(path, Path):
        path = str(path)
    zarr_location = ZarrLocation(path)
    zarr_reader = ZarrReader(zarr_location)
    zarr_image = ZarrImage(zarr_location)
    for zarr_node in zarr_reader():
        if Label.matches(zarr_location):
            try:
                label = Label(zarr_node)
            except Exception:
                continue
            for zarr_labels_layer in _read_zarr_label_image(zarr_image, label):
                zarr_image.append_layer(zarr_labels_layer)
        elif Multiscales.matches(zarr_location):
            try:
                multiscales = Multiscales(zarr_node)
            except Exception:
                continue
            for zarr_image_layer in _read_zarr_multiscales_image(
                zarr_image, multiscales
            ):
                zarr_image.append_layer(zarr_image_layer)
    return zarr_image


def _read_zarr_label_image(
    zarr_image: ZarrImage, label: Label
) -> Generator[ZarrLabelsLayer, None, None]:
    raise NotImplementedError()  # TODO


def _read_zarr_multiscales_image(
    zarr_image: ZarrImage, multiscales: Multiscales
) -> Generator[ZarrImageLayer, None, None]:
    data = [multiscales.array(dataset, "") for dataset in multiscales.datasets]
    if len(data) == 0:
        raise ZarrReaderError(f"{zarr_image} does not contain any data")
    channel_axes = [
        axis
        for axis, axis_dict in enumerate(multiscales.node.metadata["axes"])
        if axis_dict.get("type") == "channel"
    ]
    yield from _read_multiscales_image_recursion(
        zarr_image, multiscales, data, [], [], channel_axes
    )


def _read_multiscales_image_recursion(
    zarr_image: ZarrImage,
    multiscales: Multiscales,
    data: List[da.Array],
    visited_channel_axes: List[int],
    visited_channel_axis_indices: List[int],
    remaining_channel_axes: List[int],
) -> Generator[ZarrImageLayer, None, None]:
    if len(remaining_channel_axes) > 0:
        channel_axis = remaining_channel_axes[0]
        channel_axis_name = multiscales.node.metadata["axes"][channel_axis]["name"]
        channel_names = multiscales.node.metadata.get("name")
        for channel_axis_index in range(data[0].shape[channel_axis]):
            for layer in _read_multiscales_image_recursion(
                zarr_image,
                multiscales,
                data,
                visited_channel_axes + [channel_axis],
                visited_channel_axis_indices + [channel_axis_index],
                remaining_channel_axes[1:],
            ):
                layer.name = (
                    f"{channel_axis_name}={channel_axis_index} {layer.name}".rstrip()
                )
                layer.metadata[channel_axis_name] = channel_axis_index
                if channel_names and len(channel_names) == data[0].shape[channel_axis]:
                    layer.metadata["Channel"] = channel_names[channel_axis_index]
                yield layer
    else:
        layer_data = [
            np.take(x, visited_channel_axis_indices, axis=visited_channel_axes)
            for x in data
        ]
        yield ZarrImageLayer("", zarr_image, layer_data)


def load_zarr_layer(viewer: Viewer, layer: Layer) -> NapariLayer:
    if isinstance(layer, ZarrImageLayer):
        if len(layer.data) == 1:
            return viewer.add_image(data=layer.data[0], name=layer.name)
        return viewer.add_image(data=layer.data, name=layer.name, multiscale=True)
    raise ZarrReaderError(f"Unsupported layer type: {type(layer)}")
