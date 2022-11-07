from typing import Optional, Set

from napari.utils.events import Event, EventedList
from qtpy.QtCore import QItemSelection, QItemSelectionModel, QItemSelectionRange
from qtpy.QtWidgets import QHeaderView, QTreeView, QWidget

from .._controller import DatasetController
from ..model import Dataset
from ._dataset_tree_model import QDatasetTreeModel


class QDatasetTreeView(QTreeView):
    def __init__(
        self, controller: DatasetController, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._model = QDatasetTreeModel(controller)
        self._updating_selected_datasets = False
        self._updating_tree_view_selection = False
        self.setModel(self._model)
        self.header().hide()
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            QDatasetTreeModel.COLUMNS.NAME, QHeaderView.ResizeMode.Stretch
        )
        self.header().setSectionResizeMode(
            QDatasetTreeModel.COLUMNS.LOADED, QHeaderView.ResizeMode.ResizeToContents
        )
        self.header().setSectionResizeMode(
            QDatasetTreeModel.COLUMNS.VISIBLE, QHeaderView.ResizeMode.ResizeToContents
        )
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.selected_datasets.events.connect(
            self._on_selected_datasets_event
        )

    def _disconnect_events(self) -> None:
        self._controller.selected_datasets.events.disconnect(
            self._on_selected_datasets_event
        )

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._updating_tree_view_selection:
            old_selected_datasets = set(self._controller.selected_datasets)
            new_selected_datasets: Set[Dataset] = set()
            for index in self.selectionModel().selectedRows():
                dataset = index.internalPointer()
                assert isinstance(dataset, Dataset)
                new_selected_datasets.add(dataset)
            self._updating_selected_datasets = True
            try:
                for dataset in old_selected_datasets.difference(new_selected_datasets):
                    self._controller.selected_datasets.remove(dataset)
                for dataset in new_selected_datasets.difference(old_selected_datasets):
                    self._controller.selected_datasets.append(dataset)
            finally:
                self._updating_selected_datasets = False

    def _on_selected_datasets_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if (
            event.type in ("inserted", "removed", "changed")
            and not self._updating_selected_datasets
        ):
            new_item_selection = QItemSelection()
            for dataset in self._controller.selected_datasets:
                assert isinstance(dataset, Dataset)
                index = self._model.create_dataset_index(dataset)
                new_item_selection.append(QItemSelectionRange(index))
            self._updating_tree_view_selection = True
            try:
                self.selectionModel().select(
                    new_item_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect
                )
            finally:
                self._updating_tree_view_selection = False
