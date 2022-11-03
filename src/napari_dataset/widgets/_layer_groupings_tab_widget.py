from typing import Dict, List, Optional

from napari.utils.events import Event
from qtpy.QtWidgets import QTabWidget, QWidget

from .._controller import DatasetController
from ..model import Layer
from ._layer_grouping_list_view import QLayerGroupingListView


class QLayerGroupingsTabWidget(QTabWidget):
    def __init__(
        self, controller: DatasetController, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._layer_grouping_list_views: Dict[str, QLayerGroupingListView] = {}
        assert controller.viewer is not None
        self.addTab(controller.viewer.window.qt_viewer.layers, "Layer")  # TODO
        for layer in controller.layers:
            self._add_layer_groupings(layer)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.layers.events.inserted.connect(self._on_layers_inserted_event)
        self._controller.layers.events.changed.connect(self._on_layers_changed_event)

    def _disconnect_events(self) -> None:
        self._controller.layers.events.changed.disconnect(self._on_layers_changed_event)
        self._controller.layers.events.inserted.disconnect(
            self._on_layers_inserted_event
        )

    def _on_layers_inserted_event(self, event: Event) -> None:
        assert isinstance(event.value, Layer)
        self._add_layer_groupings(event.value)

    def _on_layers_changed_event(self, event: Event) -> None:
        if isinstance(event.value, Layer):
            self._add_layer_groupings(event.value)
        else:
            assert isinstance(event.value, List)
            for layer in event.value:
                assert isinstance(layer, Layer)
                self._add_layer_groupings(layer)

    def _on_close_requested(self, grouping: str) -> None:
        layer_grouping_list_view = self._layer_grouping_list_views[grouping]
        tab_index = self.indexOf(layer_grouping_list_view)
        self.removeTab(tab_index)

    def _add_layer_groupings(self, layer: Layer) -> None:
        for grouping in layer.groups.keys():
            if grouping not in self._layer_grouping_list_views:
                layer_grouping_list_view = QLayerGroupingListView(
                    self._controller,
                    grouping=grouping,
                    close_callback=lambda: self._on_close_requested(grouping),
                )
                self.addTab(layer_grouping_list_view, grouping)
                self._layer_grouping_list_views[grouping] = layer_grouping_list_view
