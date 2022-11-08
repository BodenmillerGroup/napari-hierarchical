import os
from pathlib import Path
from typing import Generator, Union

import numpy as np
from napari.layers import Image as NapariImageLayer
from napari.layers import Labels as NapariLabelsLayer

from napari_dataset.model import Dataset

from .model import OMEZarrImageLayer, OMEZarrLabelsLayer

try:
    import ome_zarr
    from ome_zarr.io import ZarrLocation
    from ome_zarr.reader import Label, Labels, Multiscales
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
            name = f"{file_name} [C{channel_index:02d}]"
            channel_data = [np.take(a, channel_index, axis=channel_axis) for a in data]
            napari_layer = NapariImageLayer(
                name=name, data=channel_data, multiscale=True
            )
            layer = OMEZarrImageLayer(
                name=name,
                loaded_napari_layer=napari_layer,
                ome_zarr_file=str(path),
                channel_axis=channel_axis,
                channel_index=channel_index,
            )
            if channel_names is not None and len(channel_names) == num_channels:
                channel_name = f"[C{channel_index:02d}] channel_names[channel_index]"
            else:
                channel_name = f"[C{channel_index:02d}] Channel {channel_index}"
            layer.groups["Channel"] = channel_name
            yield layer
    else:
        napari_layer = NapariImageLayer(name=file_name, data=data, multiscale=True)
        layer = OMEZarrImageLayer(
            name=file_name, loaded_napari_layer=napari_layer, ome_zarr_file=str(path)
        )
        yield layer


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
                label_zarr_location = ZarrLocation(
                    labels_zarr_node.zarr.subpath(label_name)
                )
                if label_zarr_location.exists() and Label.matches(label_zarr_location):
                    label_zarr_reader = ZarrReader(label_zarr_location)
                    label_zarr_node = ZarrNode(label_zarr_location, label_zarr_reader)
                    label_multiscales = Multiscales(label_zarr_node)
                    name = f"{file_name} [{label_name}]"
                    data = [
                        label_multiscales.array(resolution, "")
                        for resolution in label_multiscales.datasets
                    ]
                    napari_layer = NapariLabelsLayer(
                        name=name, data=data, multiscale=True
                    )
                    layer = OMEZarrLabelsLayer(
                        name=name,
                        loaded_napari_layer=napari_layer,
                        ome_zarr_file=str(path),
                        label_name=label_name,
                    )
                    layer.groups["Label"] = label_name
                    yield layer
