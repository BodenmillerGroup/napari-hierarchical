import os
from pathlib import Path
from typing import Optional, Union

from napari.layers import Layer as NapariLayer
from napari.viewer import Viewer

from napari_bioimage.model import Image, ImageGroup, Layer

from .model import HDF5Layer

try:
    import dask.array as da
    import h5py
except ModuleNotFoundError:
    pass  # skipped intentionally

PathLike = Union[str, os.PathLike]


def read_hdf5_image(path: PathLike) -> Image:
    with h5py.File(path) as f:
        return _create_image_group(Path(path).name, f)


def _create_image(
    name: str, dataset: "h5py.Dataset", parent: Optional[ImageGroup] = None
) -> Image:
    image = Image(name=name, parent=parent)
    layer = HDF5Layer(
        name=f"{Path(dataset.file.filename).name} [{dataset.name}]",
        image=image,
        data=da.from_array(dataset),
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


def load_hdf5_layer(layer: Layer, viewer: Viewer) -> NapariLayer:
    if isinstance(layer, HDF5Layer):
        return viewer.add_image(data=layer.data, name=layer.name)
    raise TypeError(f"Unsupported layer type: {type(layer)}")
