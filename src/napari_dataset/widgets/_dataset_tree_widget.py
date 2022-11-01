from typing import Optional, Set, Union

from napari.utils.events import Event
from qtpy.QtCore import QItemSelection, Qt
from qtpy.QtWidgets import QTreeView, QVBoxLayout, QWidget

from .._controller import DatasetController
from ..model import Dataset, Layer
from ._dataset_tree_model import QDatasetTreeModel


class QDatasetTreeWidget(QWidget):
    def __init__(
        self,
        controller: DatasetController,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self._dataset_tree_view = QTreeView()
        self._dataset_tree_model = QDatasetTreeModel(controller)
        self._dataset_tree_view.setModel(self._dataset_tree_model)
        self._ignore_dataset_tree_view_selection_changed = False
        self._ignore_layer_selection_changed_events = False
        self._setup_ui()
        self._connect_events()
        self._dataset_tree_view.selectionModel().selectionChanged.connect(
            self._on_dataset_tree_view_selection_changed
        )

    def __del__(self) -> None:
        self._disconnect_events()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        self._dataset_tree_view.setHeaderHidden(True)
        self._dataset_tree_view.setSelectionMode(
            QTreeView.SelectionMode.ExtendedSelection
        )
        self._dataset_tree_view.setDragEnabled(True)
        self._dataset_tree_view.setAcceptDrops(True)
        self._dataset_tree_view.setDropIndicatorShown(True)
        self._dataset_tree_view.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        layout.addWidget(self._dataset_tree_view)
        self.setLayout(layout)

    def _connect_events(self) -> None:
        self._controller.layers.selection.events.changed.connect(
            self._on_layers_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        self._controller.layers.selection.events.changed.disconnect(
            self._on_layers_selection_changed_event
        )

    def _on_dataset_tree_view_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._ignore_dataset_tree_view_selection_changed:
            selected_layers: Set[Layer] = set()
            for index in self._dataset_tree_view.selectionModel().selectedRows():
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
            self._ignore_dataset_tree_view_selection_changed = True
            try:
                self._dataset_tree_view.selectionModel().clear()
            finally:
                self._ignore_dataset_tree_view_selection_changed = False
