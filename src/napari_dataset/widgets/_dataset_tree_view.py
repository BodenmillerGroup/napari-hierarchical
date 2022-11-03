from typing import Optional, Set

from napari.utils.events import Event
from qtpy.QtCore import QItemSelection, QItemSelectionModel, QItemSelectionRange
from qtpy.QtWidgets import QTreeView, QWidget

from .._controller import DatasetController
from ..model import Dataset, Layer
from ._dataset_tree_model import QDatasetTreeModel


class QDatasetTreeView(QTreeView):
    def __init__(
        self, controller: DatasetController, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._model = QDatasetTreeModel(controller)
        self._ignore_layer_selection_changed_events = False
        self._ignore_selection_changed = False
        self.setModel(self._model)
        self.setHeaderHidden(True)
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.layers.selection.events.changed.connect(
            self._on_layers_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        self._controller.layers.selection.events.changed.disconnect(
            self._on_layers_selection_changed_event
        )

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._ignore_selection_changed:
            selected_layers: Set[Layer] = set()
            for index in self.selectionModel().selectedRows():
                dataset = index.internalPointer()
                assert isinstance(dataset, Dataset)
                selected_layers.update(dataset.iter_layers(recursive=True))
            self._ignore_layer_selection_changed_events = True
            try:
                self._controller.layers.selection = selected_layers
            finally:
                self._ignore_layer_selection_changed_events = False

    def _on_layers_selection_changed_event(self, event: Event) -> None:
        if not self._ignore_layer_selection_changed_events:
            selection = QItemSelection()
            for selected_layer in self._controller.layers.selection:
                if selected_layer.dataset.parent is not None:
                    row = selected_layer.dataset.parent.children.index(
                        selected_layer.dataset
                    )
                else:
                    row = self._controller.datasets.index(selected_layer.dataset)
                index = self._model.createIndex(row, 0, object=selected_layer.dataset)
                selection.append(QItemSelectionRange(index))
            self._ignore_selection_changed = True
            try:
                self.selectionModel().select(
                    selection, QItemSelectionModel.SelectionFlag.ClearAndSelect
                )
            finally:
                self._ignore_selection_changed = False
