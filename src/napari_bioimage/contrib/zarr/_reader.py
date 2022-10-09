import os
from pathlib import Path
from typing import Optional, Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, ImageGroup, Layer

from .model import ZarrLayer

try:
    import dask.array as da
    import zarr
except ModuleNotFoundError:
    pass  # ignored intentionally

PathLike = Union[str, os.PathLike]


def read_zarr_image(path: PathLike) -> Image:
    z = zarr.open(store=path, mode="r")
    if isinstance(z, zarr.Array):
        return _create_image(Path(path).name, z)
    if isinstance(z, zarr.Group):
        return _create_image_group(Path(path).name, z)
    raise TypeError(f"Unsupported zarr type: {type(z)}")


def _create_image(
    name: str, array: "zarr.Array", parent: Optional[ImageGroup] = None
) -> Image:
    image = Image(name=name, parent=parent)
    layer = ZarrLayer(
        name=f"{Path(array.path).name} [{array.name}]",
        image=image,
        data=da.from_zarr(array),
    )
    image.layers.append(layer)
    return image


def _create_image_group(
    name: str, group: "zarr.Group", parent: Optional[ImageGroup] = None
) -> ImageGroup:
    image_group = ImageGroup(name=name, parent=parent)
    for child_group_name, child_group in group.groups():
        child_image_group = _create_image_group(
            child_group_name, child_group, parent=image_group
        )
        image_group.children.append(child_image_group)
    for child_array_name, child_array in group.arrays():
        child_image = _create_image(child_array_name, child_array, parent=image_group)
        image_group.children.append(child_image)
    return image_group


def load_zarr_layer(layer: Layer, viewer: Viewer) -> NapariLayer:
    if isinstance(layer, ZarrLayer):
        return viewer.add_image(data=layer.data, name=layer.name)
    raise TypeError(f"Unsupported layer type: {type(layer)}")
