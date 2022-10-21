import os
from pathlib import Path
from typing import Optional, Union

from napari_bioimage.model import Image, ImageGroup

from .model import ZarrLayer

try:
    import zarr
except ModuleNotFoundError:
    zarr = None

PathLike = Union[str, os.PathLike]


def read_zarr(path: PathLike) -> Image:
    zarr_file = Path(path)
    while zarr_file is not None and zarr_file.suffix != ".zarr":
        zarr_file = zarr_file.parent
    assert zarr_file is not None
    z = zarr.open(store=path, mode="r")
    name = str(Path(path).relative_to(zarr_file.parent))
    if isinstance(z, zarr.Array):
        return _create_image(name, z)
    if isinstance(z, zarr.Group):
        return _create_image_group(name, z)
    raise TypeError(f"Unsupported zarr type: {type(z)}")


def _create_image(
    name: str, array: "zarr.Array", parent: Optional[ImageGroup] = None
) -> Image:
    image = Image(name=name, parent=parent)
    layer = ZarrLayer(
        name=f"{Path(array.path).name} [{array.name}]",
        image=image,
        zarr_file=array.path,
        path=array.name,
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
