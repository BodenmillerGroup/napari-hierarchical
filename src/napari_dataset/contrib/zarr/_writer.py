import os
from typing import Union

from napari.layers import Layer as NapariLayer

from napari_dataset.model import Dataset, Layer

PathLike = Union[str, os.PathLike]


def write_zarr_dataset(path: PathLike, dataset: Dataset) -> None:
    raise NotImplementedError()  # TODO


def save_zarr_layer(layer: Layer, napari_layer: NapariLayer) -> None:
    raise NotImplementedError()  # TODO
