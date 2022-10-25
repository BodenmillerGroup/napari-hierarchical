from typing import Dict, List, Mapping, Optional, Sequence, Union

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
        self._layer_identity_grouping_widget = QLayerGroupingWidget()
        self._layer_grouping_widgets: Dict[str, QLayerGroupingWidget] = {}
        self._setup_ui()
        self._layer_groupings_tab_widget.addTab(
            self._layer_identity_grouping_widget, "Layer"
        )
        for layer in controller.layers:
            self._add_layer(layer)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_groupings_tab_widget)
        self.setLayout(layout)

    def _connect_events(self) -> None:
        self._controller.layers.events.connect(self._on_layers_changed)
        for layer in self._controller.layers:
            self._connect_layer_events(layer)

    def _disconnect_events(self) -> None:
        for layer in self._controller.layers:
            self._disconnect_layer_events(layer)
        self._controller.layers.events.disconnect(self._on_layers_changed)

    def _connect_layer_events(self, layer: Layer) -> None:
        layer.events.connect(self._on_layer_changed)
        assert layer._groups_callback is None
        layer._groups_callback = layer.groups.events.connect(
            lambda event: self._on_layer_groups_changed(event, layer)
        )

    def _disconnect_layer_events(self, layer: Layer) -> None:
        layer.events.disconnect(self._on_layer_changed)
        assert layer._groups_callback is not None
        layer.groups.events.disconnect(layer._groups_callback)
        layer._groups_callback = None

    def _on_layers_changed(self, event: Event) -> None:
        if not isinstance(event.sources[0], Sequence):
            return
        layers = event.source
        assert isinstance(layers, Sequence)
        if event.type == "inserted":
            assert isinstance(event.value, Layer)
            self._add_layer(event.value)
            self._connect_layer_events(event.value)
        elif event.type == "removed":
            assert isinstance(event.value, Layer)
            self._disconnect_layer_events(event.value)
            self._remove_layer(event.value)
        elif event.type == "changed" and isinstance(event.index, int):
            assert isinstance(event.old_value, Layer)
            self._disconnect_layer_events(event.old_value)
            self._remove_layer(event.old_value)
            assert isinstance(event.value, Layer)
            self._add_layer(event.value)
            self._connect_layer_events(event.value)
        elif event.type == "changed" and isinstance(event.index, slice):
            assert isinstance(event.old_value, List)
            for old_layer in event.old_value:
                assert isinstance(old_layer, Layer)
                self._disconnect_layer_events(old_layer)
                self._remove_layer(old_layer)
            assert isinstance(event.value, List)
            for layer in event.value:
                assert isinstance(layer, Layer)
                self._add_layer(layer)
                self._connect_layer_events(layer)

    def _on_layer_changed(self, event: Event) -> None:
        pass  # TODO

    def _on_layer_groups_changed(self, event: Event, layer: Layer) -> None:
        if not isinstance(event.sources[0], Mapping):
            return
        pass  # TODO

    def _add_layer(self, layer: Layer) -> None:
        self._layer_identity_grouping_widget.add_layer(layer)
        for grouping in layer.groups.keys():
            layer_grouping_widget = self._layer_grouping_widgets.get(grouping)
            if layer_grouping_widget is None:
                layer_grouping_widget = QLayerGroupingWidget(grouping=grouping)
                self._layer_grouping_widgets[grouping] = layer_grouping_widget
                self._layer_groupings_tab_widget.addTab(layer_grouping_widget, grouping)
            layer_grouping_widget.add_layer(layer)

    def _remove_layer(self, layer: Layer) -> None:
        self._layer_identity_grouping_widget.remove_layer(layer)
        for grouping in layer.groups.keys():
            layer_grouping_widget = self._layer_grouping_widgets[grouping]
            layer_grouping_widget.remove_layer(layer)
            if len(layer_grouping_widget.group_layers) == 0:
                index = self._layer_groupings_tab_widget.indexOf(layer_grouping_widget)
                self._layer_groupings_tab_widget.removeTab(index)
