from typing import Callable, Optional, Set

from napari.utils.events import Event
from qtpy.QtCore import QItemSelection, QItemSelectionModel, QItemSelectionRange
from qtpy.QtWidgets import QListView, QWidget

from .._controller import DatasetController
from ..model import Layer
from ._layer_grouping_list_model import QLayerGroupingListModel


class QLayerGroupingListView(QListView):
    def __init__(
        self,
        controller: DatasetController,
        grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._grouping = grouping
        self._close_callback = close_callback
        self._model = QLayerGroupingListModel(
            controller, grouping=grouping, close_callback=close_callback
        )
        self._ignore_layers_selection_changed_events = False
        self._ignore_selection_changed = False
        self.setModel(self._model)
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
                group = self._model.groups[index.row()]
                group_layers = self._model.group_layers[group]
                selected_layers.update(group_layers)
            self._ignore_layers_selection_changed_events = True
            try:
                self._controller.layers.selection = selected_layers
            finally:
                self._ignore_layers_selection_changed_events = False

    def _on_layers_selection_changed_event(self, event: Event) -> None:
        if not self._ignore_layers_selection_changed_events:
            selection = QItemSelection()
            selected_groups = []
            for selected_layer in self._controller.layers.selection:
                if self._grouping in selected_layer.groups:
                    selected_group = selected_layer.groups[self._grouping]
                    if selected_group not in selected_groups:
                        row = self._model.groups.index(selected_group)
                        index = self._model.createIndex(row, 0)
                        selection.append(QItemSelectionRange(index))
                        selected_groups.append(selected_group)
            self._ignore_selection_changed = True
            try:
                self.selectionModel().select(
                    selection, QItemSelectionModel.SelectionFlag.ClearAndSelect
                )
            finally:
                self._ignore_selection_changed = False
