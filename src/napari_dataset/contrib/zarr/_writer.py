import os
from typing import Union

from napari_dataset.model import Dataset, Layer

PathLike = Union[str, os.PathLike]


def write_zarr_dataset(path: PathLike, dataset: Dataset) -> None:
    raise NotImplementedError()  # TODO


def save_zarr_layer(layer: Layer) -> None:
    raise NotImplementedError()  # TODO
