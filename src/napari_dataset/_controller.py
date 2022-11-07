import os
from typing import Optional, Set, Union

from napari.layers import Layer as NapariLayer
from napari.utils.events import Event, EventedList, SelectableEventedList
from napari.viewer import Viewer
from pluggy import PluginManager

from . import hookspecs
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
        self._selected_datasets: EventedList[Dataset] = EventedList(
            basetype=Dataset, lookup={str: lambda dataset: dataset.name}
        )
        self._current_layers: SelectableEventedList[Layer] = SelectableEventedList(
            basetype=Layer, lookup={str: lambda layer: layer.name}
        )
        self._updating_viewer_layers_selection = False
        self._updating_current_layers_selection = False
        self._datasets.events.connect(self._on_datasets_event)
        self._selected_datasets.events.connect(self._on_selected_datasets_event)
        self._current_layers.selection.events.changed.connect(
            self._on_current_layers_selection_changed_event
        )

    def __del__(self) -> None:
        if self._viewer is not None:
            self._viewer.layers.selection.events.changed.disconnect(
                self._on_viewer_layers_selection_changed_event
            )

    def register_viewer(self, viewer: Viewer) -> None:
        assert self._viewer is None
        self._viewer = viewer
        viewer.layers.selection.events.changed.connect(
            self._on_viewer_layers_selection_changed_event
        )

    def can_read_dataset(self, path: PathLike) -> bool:
        dataset_reader_function = self._get_dataset_reader_function(path)
        return dataset_reader_function is not None

    def can_write_dataset(self, path: PathLike, dataset: Dataset) -> bool:
        dataset_writer_function = self._get_dataset_writer_function(path, dataset)
        return dataset_writer_function is not None

    def can_load_dataset(self, dataset: Dataset) -> bool:
        for layer in dataset.iter_layers(recursive=True):
            if not self.can_load_layer(layer):
                return False
        return True

    def can_save_dataset(self, dataset: Dataset) -> bool:
        for layer in dataset.iter_layers(recursive=True):
            if not self.can_save_layer(layer):
                return False
        return True

    def can_load_layer(self, layer: Layer) -> bool:
        layer_loader_function = self._get_layer_loader_function(layer)
        return layer_loader_function is not None

    def can_save_layer(self, layer: Layer) -> bool:
        layer_saver_function = self._get_layer_saver_function(layer)
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
        return dataset

    def write_dataset(self, path: PathLike, dataset: Dataset) -> None:
        dataset_writer_function = self._get_dataset_writer_function(path, dataset)
        if dataset_writer_function is None:
            raise DatasetControllerException(f"No dataset writer found for {path}")
        try:
            dataset_writer_function(path, dataset)
        except Exception as e:
            raise DatasetControllerException(e)

    def load_dataset_layers(self, dataset: Dataset) -> None:
        if not self.can_load_dataset(dataset):
            raise DatasetControllerException(f"Dataset cannot be loaded: {dataset}")
        for layer in dataset.iter_layers(recursive=True):
            self.load_layer(layer)

    def save_dataset_layers(self, dataset: Dataset) -> None:
        if not self.can_save_dataset(dataset):
            raise DatasetControllerException(f"Dataset cannot be loaded: {dataset}")
        for layer in dataset.iter_layers(recursive=True):
            self.save_layer(layer)

    def close_dataset_layers(self, dataset: Dataset) -> None:
        for layer in dataset.iter_layers(recursive=True):
            self.close_layer(layer)

    def load_layer(self, layer: Layer) -> None:
        layer_loader_function = self._get_layer_loader_function(layer)
        if layer_loader_function is None:
            raise DatasetControllerException(f"No layer loader found for {layer}")
        try:
            layer_loader_function(layer)
        except Exception as e:
            raise DatasetControllerException(e)
        if layer.napari_layer is not None:
            assert self._viewer is not None
            self._viewer.add_layer(layer.napari_layer)

    def save_layer(self, layer: Layer) -> None:
        if layer.napari_layer is None:
            raise DatasetControllerException(f"Layer is not loaded: {layer}")
        layer_saver_function = self._get_layer_saver_function(layer)
        if layer_saver_function is None:
            raise DatasetControllerException(f"No layer saver found for {layer}")
        try:
            layer_saver_function(layer)
        except Exception as e:
            raise DatasetControllerException(e)

    def close_layer(self, layer: Layer) -> None:
        if layer.napari_layer is not None:
            if self._viewer is not None and layer.napari_layer in self._viewer.layers:
                self._viewer.layers.remove(layer.napari_layer)
            layer.napari_layer = None

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
        self, layer: Layer
    ) -> Optional[hookspecs.LayerSaverFunction]:
        layer_saver_function = self._pm.hook.napari_dataset_get_layer_saver(layer=layer)
        return layer_saver_function

    def _on_datasets_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type in ("inserted", "removed", "changed"):
            if len(self._selected_datasets) > 0:
                self._selected_datasets.clear()
            else:
                self._update_current_layers()

    def _on_selected_datasets_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type in ("inserted", "removed", "changed"):
            self._update_current_layers()

    def _update_current_layers(self) -> None:
        if len(self._selected_datasets) > 0:
            datasets = self._selected_datasets
        else:
            datasets = self._datasets
        old_current_layers = set(self._current_layers)
        new_current_layers: Set[Layer] = set()
        for dataset in datasets:
            assert isinstance(dataset, Dataset)
            new_current_layers.update(dataset.iter_layers(recursive=True))
        for layer in old_current_layers.difference(new_current_layers):
            self._current_layers.remove(layer)
        for layer in new_current_layers.difference(old_current_layers):
            self._current_layers.append(layer)

    def _on_current_layers_selection_changed_event(self, event: Event) -> None:
        if self._viewer is not None and not self._updating_current_layers_selection:
            new_viewer_layers_selection: Set[NapariLayer] = set()
            for layer in self._current_layers.selection:
                assert isinstance(layer, Layer)
                if (
                    layer.napari_layer is not None
                    and layer.napari_layer in self._viewer.layers
                ):
                    new_viewer_layers_selection.add(layer.napari_layer)
            self._updating_viewer_layers_selection = True
            try:
                self._viewer.layers.selection = new_viewer_layers_selection
            finally:
                self._updating_viewer_layers_selection = False

    def _on_viewer_layers_selection_changed_event(self, event: Event) -> None:
        if self._viewer is not None and not self._updating_viewer_layers_selection:
            new_current_layers_selection: Set[Layer] = set()
            for napari_layer in self._viewer.layers.selection:
                assert isinstance(napari_layer, NapariLayer)
                layer = next(
                    (
                        layer
                        for dataset in self._datasets
                        for layer in dataset.iter_layers(recursive=True)
                        if layer.napari_layer == napari_layer
                    ),
                    None,
                )
                if layer is not None and layer in self._current_layers:
                    new_current_layers_selection.add(layer)
            self._updating_current_layers_selection = True
            try:
                self._current_layers.selection = new_current_layers_selection
            finally:
                self._updating_current_layers_selection = False

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
    def selected_datasets(self) -> EventedList[Dataset]:
        return self._selected_datasets

    @property
    def current_layers(self) -> SelectableEventedList[Layer]:
        return self._current_layers


class DatasetControllerException(Exception):
    pass


controller = DatasetController()
