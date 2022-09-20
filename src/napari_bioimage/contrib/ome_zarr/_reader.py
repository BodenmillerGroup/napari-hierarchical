import os
from typing import Generator, List, Sequence, Union

import numpy as np
from dask.array import Array
from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, Layer

from ._exceptions import BioImageOMEZarrException
from .model import OMEZarrImage, OMEZarrImageLayer, OMEZarrLabelsLayer

try:
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Multiscales
    from ome_zarr.reader import Reader as ZarrReader
except ModuleNotFoundError:
    pass  # skipped intentionally

PathLike = Union[str, os.PathLike]


def read_ome_zarr_image(path: PathLike) -> Image:
    zarr_location = ZarrLocation(str(path))
    try:
        zarr_reader = ZarrReader(zarr_location)
        zarr_node = next(zarr_reader())  # first node is the image pixel data
        multiscales = Multiscales(zarr_node)
    except Exception as e:
        raise BioImageOMEZarrException(e)
    if "axes" not in multiscales.node.metadata:
        raise BioImageOMEZarrException(f"{path} does not contain axes metadata")
    try:
        data = [multiscales.array(dataset, "") for dataset in multiscales.datasets]
    except Exception as e:
        raise BioImageOMEZarrException(e)
    if len(data) == 0:
        raise BioImageOMEZarrException(f"{path} does not contain any data")
    channel_axes = [
        axis
        for axis, axis_dict in enumerate(multiscales.node.metadata["axes"])
        if axis_dict.get("type") == "channel"
    ]
    ome_zarr_image = OMEZarrImage(name=str(path))
    for zarr_image_layer in _read_ome_zarr_image_layers(
        ome_zarr_image, multiscales, data, channel_axes
    ):
        ome_zarr_image.layers.append(zarr_image_layer)
    return ome_zarr_image


def _read_ome_zarr_image_layers(
    ome_zarr_image: OMEZarrImage,
    multiscales: "Multiscales",
    data: List[Array],
    channel_axes: Sequence[int],
    _current_channel_axes: Sequence[int] = (),
    _current_channel_indices: Sequence[int] = (),
) -> Generator[OMEZarrImageLayer, None, None]:
    if len(channel_axes) > 0:
        channel_axis = channel_axes[0]
        channel_axis_name = multiscales.node.metadata["axes"][channel_axis].get("name")
        if channel_axis_name is None:
            raise BioImageOMEZarrException(
                f"{ome_zarr_image} does not contain name of channel axis {channel_axis}"
            )
        channel_names = multiscales.node.metadata.get("name")
        for channel_index in range(data[0].shape[channel_axis]):
            for layer in _read_ome_zarr_image_layers(
                ome_zarr_image,
                multiscales,
                data,
                channel_axes[1:],
                list(_current_channel_axes) + [channel_axis],
                list(_current_channel_indices) + [channel_index],
            ):
                layer_name_prefix = f"{channel_axis_name}={channel_index}"
                if layer.name:
                    layer.name = f"{layer_name_prefix} {layer.name}"
                else:
                    layer.name = layer_name_prefix
                layer.metadata[channel_axis_name] = channel_index
                if channel_names and len(channel_names) == data[0].shape[channel_axis]:
                    layer.metadata["Channel"] = channel_names[channel_index]
                yield layer
    else:

        def take_channels(a: Array) -> Array:
            for channel_axis, channel_index in sorted(
                zip(_current_channel_axes, _current_channel_indices),
                key=lambda axis_and_index: axis_and_index[0],
                reverse=True,
            ):
                a = np.take(a, channel_index, axis=channel_axis)
            return a

        layer_data = [take_channels(a) for a in data]
        yield OMEZarrImageLayer(name="", image=ome_zarr_image, data=layer_data)


def load_ome_zarr_layer(layer: Layer, viewer: Viewer) -> NapariLayer:
    if isinstance(layer, OMEZarrLabelsLayer):
        pass  # TODO zarr labels layers
    elif isinstance(layer, OMEZarrImageLayer):
        if len(layer.data) == 1:
            return viewer.add_image(data=layer.data[0], name=layer.name)
        return viewer.add_image(data=layer.data, name=layer.name, multiscale=True)
    raise BioImageOMEZarrException(f"Unsupported layer type: {type(layer)}")
