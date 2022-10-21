import os
from pathlib import Path
from typing import Generator, Union

from napari_bioimage.model import Image

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


def read_ome_zarr(path: PathLike) -> Image:
    image = Image(name=Path(path).name)
    for image_layer in _get_image_layers(path, image):
        image.layers.append(image_layer)
    for labels_layer in _get_labels_layers(path, image):
        image.layers.append(labels_layer)
    return image


def _get_image_layers(
    path: PathLike, image: Image
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
        raise ValueError(f"{image} contains multiple channel axes")
    if channel_axis is not None:
        data = [multiscales.array(res, "") for res in multiscales.datasets]
        if len(data) == 0:
            raise ValueError(f"{image} does not contain any data")
        num_channels = data[0].shape[channel_axis]
        if any(a.shape[channel_axis] != num_channels for a in data):
            raise ValueError(
                f"{image} contains resolutions with inconsistent channel numbers"
            )
        for channel_index in range(num_channels):
            image_layer = OMEZarrImageLayer(
                name=f"{image.name} [C{channel_index:02d}]",
                image=image,
                ome_zarr_file=str(path),
                channel_axis=channel_axis,
                channel_index=channel_index,
            )
            if channel_names is not None and len(channel_names) == num_channels:
                image_layer.metadata["Channel"] = channel_names[channel_index]
            else:
                image_layer.metadata["Channel"] = f"Channel {channel_index}"
            yield image_layer
    else:
        image_layer = OMEZarrImageLayer(
            name=image.name, image=image, ome_zarr_file=str(path)
        )
        yield image_layer


def _get_labels_layers(
    path: PathLike, image: Image
) -> Generator[OMEZarrLabelsLayer, None, None]:
    zarr_location = ZarrLocation(str(path))
    zarr_reader = ZarrReader(zarr_location)
    for labels_zarr_node in zarr_reader():
        if (
            Labels.matches(labels_zarr_node.zarr)
            and "labels" in labels_zarr_node.zarr.root_attrs
        ):
            for label_name in labels_zarr_node.zarr.root_attrs["labels"]:
                labels_layer = OMEZarrLabelsLayer(
                    name=f"{image.name} [{label_name}]",
                    image=image,
                    ome_zarr_file=str(path),
                    label_name=label_name,
                )
                labels_layer.metadata["Label"] = label_name
                yield labels_layer
