import os
from typing import Optional, Union

from napari.layers import Layer as NapariLayer
from napari.utils.events import EventedList
from napari.viewer import Viewer
from pluggy import PluginManager

from . import hookspecs
from ._exceptions import DatasetException
from .model import Dataset, Layer

PathLike = Union[str, os.PathLike]


class DatasetController:
    def __init__(self) -> None:
        self._pm = PluginManager("napari-dataset")
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints("napari-dataset")
        self._viewer: Optional[Viewer] = None
        self._datasets: EventedList[Dataset] = EventedList(
            basetype=Dataset, lookup={str: lambda dataset: dataset.name}
        )
        self._layers: EventedList[Layer] = EventedList(
            basetype=Layer, lookup={str: lambda layer: layer.name}
        )

    def can_read_dataset(self, path: PathLike) -> bool:
        dataset_reader_function = self._get_dataset_reader_function(path)
        return dataset_reader_function is not None

    def can_write_dataset(self, path: PathLike, dataset: Dataset) -> bool:
        dataset_writer_function = self._get_dataset_writer_function(path, dataset)
        return dataset_writer_function is not None

    def can_load_layer(self, layer: Layer) -> bool:
        layer_loader_function = self._get_layer_loader_function(layer)
        return layer_loader_function is not None

    def can_save_layer(self, layer: Layer, napari_layer: NapariLayer) -> bool:
        layer_saver_function = self._get_layer_saver_function(layer, napari_layer)
        return layer_saver_function is not None

    def read_dataset(self, path: PathLike) -> Dataset:
        dataset_reader_function = self._get_dataset_reader_function(path)
        if dataset_reader_function is None:
            raise DatasetControllerException(f"No dataset reader found for {path}")
        try:
            dataset = dataset_reader_function(path)
        except Exception as e:
            raise DatasetControllerException(e)
        self._datasets.append(dataset)
        for layer in dataset.iter_layers(recursive=True):
            self._layers.append(layer)
        return dataset

    def write_dataset(self, path: PathLike, dataset: Dataset) -> None:
        dataset_writer_function = self._get_dataset_writer_function(path, dataset)
        if dataset_writer_function is None:
            raise DatasetControllerException(f"No dataset writer found for {path}")
        try:
            dataset_writer_function(path, dataset)
        except Exception as e:
            raise DatasetControllerException(e)

    def load_layer(self, layer: Layer) -> NapariLayer:
        layer_loader_function = self._get_layer_loader_function(layer)
        if layer_loader_function is None:
            raise DatasetControllerException(f"No layer loader found for {layer}")
        try:
            napari_layer = layer_loader_function(layer)
        except Exception as e:
            raise DatasetControllerException(e)
        return napari_layer

    def save_layer(self, layer: Layer, napari_layer: NapariLayer) -> None:
        layer_saver_function = self._get_layer_saver_function(layer, napari_layer)
        if layer_saver_function is None:
            raise DatasetControllerException(f"No layer saver found for {layer}")
        try:
            layer_saver_function(layer, napari_layer)
        except Exception as e:
            raise DatasetControllerException(e)

    def register_viewer(self, viewer: Viewer) -> None:
        assert self._viewer is None
        self._viewer = viewer

    def _get_dataset_reader_function(
        self, path: PathLike
    ) -> Optional[hookspecs.DatasetReaderFunction]:
        dataset_reader_function = self._pm.hook.napari_dataset_get_dataset_reader(
            path=path
        )
        return dataset_reader_function

    def _get_dataset_writer_function(
        self, path: PathLike, dataset: Dataset
    ) -> Optional[hookspecs.DatasetWriterFunction]:
        dataset_writer_function = self._pm.hook.napari_dataset_get_dataset_writer(
            path=path, dataset=dataset
        )
        return dataset_writer_function

    def _get_layer_loader_function(
        self, layer: Layer
    ) -> Optional[hookspecs.LayerLoaderFunction]:
        layer_loader_function = self._pm.hook.napari_dataset_get_layer_loader(
            layer=layer
        )
        return layer_loader_function

    def _get_layer_saver_function(
        self, layer: Layer, napari_layer: NapariLayer
    ) -> Optional[hookspecs.LayerSaverFunction]:
        layer_saver_function = self._pm.hook.napari_dataset_get_layer_saver(
            layer=layer, napari_layer=napari_layer
        )
        return layer_saver_function

    @property
    def pm(self) -> PluginManager:
        return self._pm

    @property
    def viewer(self) -> Optional[Viewer]:
        return self._viewer

    @property
    def datasets(self) -> EventedList[Dataset]:
        return self._datasets

    @property
    def layers(self) -> EventedList[Layer]:
        return self._layers


class DatasetControllerException(DatasetException):
    pass


controller = DatasetController()
