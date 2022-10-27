import os
from typing import Optional, Union

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
        # self._layers.selection.events.connect(self._on_layers_selection_event)

    def can_read(self, path: PathLike) -> bool:
        reader_function = self._get_reader_function(path)
        return reader_function is not None

    def can_write(self, path: PathLike, dataset: Dataset) -> bool:
        writer_function = self._get_writer_function(path, dataset)
        return writer_function is not None

    def read(self, path: PathLike) -> Dataset:
        reader_function = self._get_reader_function(path)
        if reader_function is None:
            raise DatasetControllerException(f"No reader found for {path}")
        try:
            dataset = reader_function(path)
        except Exception as e:
            raise DatasetControllerException(e)
        layers = dataset.get_layers(recursive=True)
        self._datasets.append(dataset)
        self._layers += layers
        return dataset

    def write(self, path: PathLike, dataset: Dataset) -> None:
        writer_function = self._get_writer_function(path, dataset)
        if writer_function is None:
            raise DatasetControllerException(f"No writer found for {path}")
        try:
            writer_function(path, dataset)
        except Exception as e:
            raise DatasetControllerException(e)

    def register_viewer(self, viewer: Viewer) -> None:
        assert self._viewer is None
        self._viewer = viewer

    def _get_reader_function(
        self, path: PathLike
    ) -> Optional[hookspecs.ReaderFunction]:
        reader_function = self._pm.hook.napari_dataset_get_reader(path=path)
        return reader_function

    def _get_writer_function(
        self, path: PathLike, dataset: Dataset
    ) -> Optional[hookspecs.WriterFunction]:
        writer_function = self._pm.hook.napari_dataset_get_writer(
            path=path, dataset=dataset
        )
        return writer_function

    # def _on_layers_selection_event(self, event: Event) -> None:
    #     if not isinstance(event.sources[0], SelectableEventedList):
    #         return
    #     if event.type in ("inserted", "removed", "changed"):
    #         self._viewer.layers.selection.clear()
    #         for layer in self.layers.selection:
    #             if layer.loaded and layer.layer in self._viewer.layers:
    #                 self._viewer.layers.selection.add(layer.layer)

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
