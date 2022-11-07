from typing import Callable, Optional, Set

from napari.utils.events import Event
from qtpy.QtCore import QItemSelection, QSortFilterProxyModel
from qtpy.QtWidgets import QHeaderView, QTableView, QWidget

from .._controller import DatasetController
from ..model import Layer
from ._layer_group_table_model import QLayerGroupTableModel


class QLayerGroupTableView(QTableView):
    def __init__(
        self,
        controller: DatasetController,
        grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._model = QLayerGroupTableModel(
            controller, grouping=grouping, close_callback=close_callback
        )
        self._ignore_layers_selection_changed_events = False
        self._ignore_selection_changed = False
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.sort(QLayerGroupTableModel.COLUMNS.NAME)
        self.setModel(self._proxy_model)
        self.verticalHeader().hide()
        self.horizontalHeader().hide()
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(
            QLayerGroupTableModel.COLUMNS.NAME, QHeaderView.ResizeMode.Stretch
        )
        self.horizontalHeader().setSectionResizeMode(
            QLayerGroupTableModel.COLUMNS.LOADED,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.horizontalHeader().setSectionResizeMode(
            QLayerGroupTableModel.COLUMNS.VISIBLE,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.current_layers.selection.events.changed.connect(
            self._on_current_layers_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        self._controller.current_layers.selection.events.changed.disconnect(
            self._on_current_layers_selection_changed_event
        )

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._ignore_selection_changed:
            new_current_layers_selection: Set[Layer] = set()
            for proxy_index in self.selectionModel().selectedRows():
                index = self._proxy_model.mapToSource(proxy_index)
                group = self._model.groups[index.row()]
                group_layers = self._model.group_layers[group]
                new_current_layers_selection.update(group_layers)
            self._ignore_layers_selection_changed_events = True
            try:
                self._controller.current_layers.selection = new_current_layers_selection
            finally:
                self._ignore_layers_selection_changed_events = False

    def _on_current_layers_selection_changed_event(self, event: Event) -> None:
        if not self._ignore_layers_selection_changed_events:
            self._ignore_selection_changed = True
            try:
                self.selectionModel().clear()
            finally:
                self._ignore_selection_changed = False
