from typing import Dict, List, Optional

from napari.utils.events import Event
from qtpy.QtWidgets import QTabWidget, QWidget

from .._controller import DatasetController
from ..model import Layer
from ._layer_group_table_view import QLayerGroupTableView


class QLayerGroupTableViewsTabWidget(QTabWidget):
    def __init__(
        self, controller: DatasetController, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._layer_group_table_views: Dict[str, QLayerGroupTableView] = {}
        assert controller.viewer is not None
        self.addTab(QLayerGroupTableView(controller), "Layer")
        for layer in controller.current_layers:
            self._add_layer(layer)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.current_layers.events.inserted.connect(
            self._on_current_layers_inserted_event
        )
        self._controller.current_layers.events.changed.connect(
            self._on_current_layers_changed_event
        )

    def _disconnect_events(self) -> None:
        self._controller.current_layers.events.inserted.disconnect(
            self._on_current_layers_inserted_event
        )
        self._controller.current_layers.events.changed.disconnect(
            self._on_current_layers_changed_event
        )

    def _on_current_layers_inserted_event(self, event: Event) -> None:
        assert isinstance(event.value, Layer)
        self._add_layer(event.value)

    def _on_current_layers_changed_event(self, event: Event) -> None:
        if isinstance(event.value, Layer):
            self._add_layer(event.value)
        else:
            assert isinstance(event.value, List)
            for layer in event.value:
                assert isinstance(layer, Layer)
                self._add_layer(layer)

    def _add_layer(self, layer: Layer) -> None:
        for grouping in layer.groups.keys():
            if grouping not in self._layer_group_table_views:
                layer_group_table_view = QLayerGroupTableView(
                    self._controller,
                    grouping=grouping,
                    close_callback=lambda: self._close_grouping(grouping),
                )
                self.addTab(layer_group_table_view, grouping)
                self._layer_group_table_views[grouping] = layer_group_table_view

    def _close_grouping(self, grouping: str) -> None:
        layer_group_table_view = self._layer_group_table_views.pop(grouping)
        layer_group_table_view_tab_index = self.indexOf(layer_group_table_view)
        self.removeTab(layer_group_table_view_tab_index)
