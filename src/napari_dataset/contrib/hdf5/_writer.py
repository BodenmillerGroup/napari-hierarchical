import os
from typing import Union

from napari_dataset.model import Dataset, Layer

PathLike = Union[str, os.PathLike]


def write_hdf5_dataset(path: PathLike, dataset: Dataset) -> None:
    raise NotImplementedError()  # TODO


def save_hdf5_layer(layer: Layer) -> None:
    raise NotImplementedError()  # TODO
