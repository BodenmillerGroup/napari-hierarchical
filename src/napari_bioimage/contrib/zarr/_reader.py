import os
from pathlib import Path
from typing import Optional, Union

from napari_bioimage.model import Image

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
    if isinstance(z, zarr.Group):
        return _create_group_image(name, z)
    if isinstance(z, zarr.Array):
        return _create_array_image(name, z)
    raise TypeError(f"Unsupported zarr type: {type(z)}")


def _create_group_image(
    name: str, group: "zarr.Group", parent: Optional[Image] = None
) -> Image:
    image = Image(name=name, parent=parent)
    for child_group_name, child_group in group.groups():
        child_image = _create_group_image(child_group_name, child_group, parent=image)
        image.children.append(child_image)
    for child_array_name, child_array in group.arrays():
        child_image = _create_array_image(child_array_name, child_array, parent=image)
        image.children.append(child_image)
    return image


def _create_array_image(
    name: str, array: "zarr.Array", parent: Optional[Image] = None
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
