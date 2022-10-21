import os
from pathlib import Path
from typing import Optional, Union

from napari_bioimage.model import Image, ImageGroup, Layer

try:
    import h5py
except ModuleNotFoundError:
    h5py = None

PathLike = Union[str, os.PathLike]


def read_hdf5(path: PathLike) -> Image:
    with h5py.File(path) as f:
        return _create_image_group(Path(path).name, f)


def _create_image(
    name: str, dataset: "h5py.Dataset", parent: Optional[ImageGroup] = None
) -> Image:
    image = Image(name=name, parent=parent)
    layer = Layer(
        name=f"{Path(dataset.file.filename).name} [{dataset.name}]",
        image=image,
        hdf5_file=dataset.file.filename,
        path=dataset.name,
    )
    image.layers.append(layer)
    return image


def _create_image_group(
    name: str, group: "h5py.Group", parent: Optional[ImageGroup] = None
) -> ImageGroup:
    image_group = ImageGroup(name=name, parent=parent)
    for child_name, child_item in group.items():
        if isinstance(child_item, h5py.Group):
            child_image_group = _create_image_group(
                child_name, child_item, parent=image_group
            )
            image_group.children.append(child_image_group)
        elif isinstance(child_item, h5py.Dataset):
            child_image = _create_image(child_name, child_item, parent=image_group)
            image_group.children.append(child_image)
    return image_group
