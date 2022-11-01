from typing import Callable, Optional, Set, Union

from napari.utils.events import Event
from qtpy.QtCore import QItemSelection, Qt
from qtpy.QtWidgets import QListView, QVBoxLayout, QWidget

from .._controller import DatasetController
from ..model import Layer
from ._layer_grouping_list_model import QLayerGroupingListModel


class QLayerGroupingListWidget(QWidget):
    def __init__(
        self,
        controller: DatasetController,
        grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self._layer_grouping_list_view = QListView()
        self._layer_grouping_list_model = QLayerGroupingListModel(
            controller, grouping=grouping, close_callback=close_callback
        )
        self._layer_grouping_list_view.setModel(self._layer_grouping_list_model)
        self._ignore_layer_grouping_list_view_selection_changed = False
        self._ignore_layers_selection_changed_events = False
        self._setup_ui()
        self._connect_events()
        self._layer_grouping_list_view.selectionModel().selectionChanged.connect(
            self._on_layer_grouping_list_view_selection_changed
        )

    def __del__(self) -> None:
        self._disconnect_events()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_grouping_list_view)
        self.setLayout(layout)

    def _connect_events(self) -> None:
        self._controller.layers.selection.events.changed.connect(
            self._on_layers_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        self._controller.layers.selection.events.changed.disconnect(
            self._on_layers_selection_changed_event
        )

    def _on_layer_grouping_list_view_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._ignore_layer_grouping_list_view_selection_changed:
            selected_layers: Set[Layer] = set()
            for index in self._layer_grouping_list_view.selectionModel().selectedRows():
                group = self._layer_grouping_list_model.groups[index.row()]
                group_layers = self._layer_grouping_list_model.group_layers[group]
                selected_layers.update(group_layers)
            self._ignore_layers_selection_changed_events = True
            try:
                self._controller.layers.selection = selected_layers
            finally:
                self._ignore_layers_selection_changed_events = False

    def _on_layers_selection_changed_event(self, event: Event) -> None:
        if not self._ignore_layers_selection_changed_events:
            self._ignore_layer_grouping_list_view_selection_changed = True
            try:
                self._layer_grouping_list_view.selectionModel().clear()
            finally:
                self._ignore_layer_grouping_list_view_selection_changed = False
