import os
from pathlib import Path
from typing import Optional, Union

from napari_bioimage.model import Image, Layer

try:
    import h5py
except ModuleNotFoundError:
    h5py = None

PathLike = Union[str, os.PathLike]


def read_hdf5(path: PathLike) -> Image:
    with h5py.File(path) as f:
        image = _create_group_image(Path(path).name, f)
    return image


def _create_group_image(
    name: str, group: "h5py.Group", parent: Optional[Image] = None
) -> Image:
    image = Image(name=name, parent=parent)
    for child_name, child_item in group.items():
        if isinstance(child_item, h5py.Group):
            child_image = _create_group_image(child_name, child_item, parent=image)
        elif isinstance(child_item, h5py.Dataset):
            child_image = _create_dataset_image(child_name, child_item, parent=image)
        else:
            raise ValueError(f"Unsupported child type: {type(child_item)}")
        image.children.append(child_image)
    return image


def _create_dataset_image(
    name: str, dataset: "h5py.Dataset", parent: Optional[Image] = None
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
