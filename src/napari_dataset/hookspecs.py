import os
from typing import Callable, Optional, Union

from napari.layers import Layer as NapariLayer
from pluggy import HookspecMarker

from .model import Dataset, Layer

PathLike = Union[str, os.PathLike]
DatasetReaderFunction = Callable[[PathLike], Dataset]
DatasetWriterFunction = Callable[[PathLike, Dataset], None]
LayerLoaderFunction = Callable[[Layer], NapariLayer]
LayerSaverFunction = Callable[[Layer, NapariLayer], None]

hookspec = HookspecMarker("napari-dataset")


@hookspec(firstresult=True)
def napari_dataset_get_dataset_reader(
    path: PathLike,
) -> Optional[DatasetReaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_dataset_get_dataset_writer(
    path: PathLike, dataset: Dataset
) -> Optional[DatasetWriterFunction]:
    pass


@hookspec(firstresult=True)
def napari_dataset_get_layer_loader(layer: Layer) -> Optional[LayerLoaderFunction]:
    pass


@hookspec(firstresult=True)
def napari_dataset_get_layer_saver(
    layer: Layer, napari_layer: NapariLayer
) -> Optional[LayerSaverFunction]:
    pass