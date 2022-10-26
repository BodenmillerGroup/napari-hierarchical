from typing import Dict, List, Optional, Union

from napari.utils.events import Event
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .._controller import BioImageController
from ..model import Layer
from ._layer_grouping_widget import QLayerGroupingWidget


class QLayerGroupingsWidget(QWidget):
    def __init__(
        self,
        controller: BioImageController,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self._layer_groupings_tab_widget = QTabWidget()
        self._layer_grouping_widgets: Dict[str, QLayerGroupingWidget] = {}
        self._setup_ui()
        for layer in controller.layers:
            self._register_layer(layer)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_groupings_tab_widget)
        self.setLayout(layout)

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
        self._register_layer(event.value)

    def _on_layers_changed_event(self, event: Event) -> None:
        if isinstance(event.value, Layer):
            self._register_layer(event.value)
        else:
            assert isinstance(event.value, List)
            for layer in event.value:
                assert isinstance(layer, Layer)
                self._register_layer(layer)

    def _on_close_requested(self, layer_grouping_widget: QLayerGroupingWidget) -> None:
        tab_index = self._layer_groupings_tab_widget.indexOf(layer_grouping_widget)
        self._layer_groupings_tab_widget.removeTab(tab_index)

    def _register_layer(self, layer: Layer) -> None:
        for grouping in layer.groups.keys():
            if grouping not in self._layer_grouping_widgets:
                layer_grouping_widget = QLayerGroupingWidget(
                    self._controller, grouping, self._on_close_requested
                )
                self._layer_groupings_tab_widget.addTab(layer_grouping_widget, grouping)
                self._layer_grouping_widgets[grouping] = layer_grouping_widget
