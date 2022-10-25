from typing import Dict, Mapping, Optional, Sequence, Union

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
        self._setup_user_interface()
        for layer in controller.layers:
            self._register_layer(layer)
        self._connect_events()

    def _setup_user_interface(self) -> None:
        layout = QVBoxLayout()
        self._layer_groupings_tab_widget.addTab(
            self._layer_identity_grouping_widget, "Layer"
        )
        layout.addWidget(self._layer_groupings_tab_widget)
        self.setLayout(layout)

    def _register_layer(self, layer: Layer) -> None:
        for grouping in layer.groups.keys():
            layer_grouping_widget = self._layer_grouping_widgets.get(grouping)
            if layer_grouping_widget is None:
                layer_grouping_widget = QLayerGroupingWidget(grouping=grouping)
                self._layer_grouping_widgets[grouping] = layer_grouping_widget
                self._layer_groupings_tab_widget.addTab(layer_grouping_widget, grouping)
            layer_grouping_widget.add_layer(layer)

    def _deregister_layer(self, layer: Layer) -> None:
        for grouping in layer.groups.keys():
            layer_grouping_widget = self._layer_grouping_widgets[grouping]
            layer_grouping_widget.remove_layer(layer)
            # TODO remove tab if empty

    def _connect_events(self) -> None:
        self._controller.layers.events.connect(self._on_layers_changed)
        for layer in self._controller.layers:
            layer._groups_callback = layer.groups.events.connect(
                lambda event: self._on_layer_groups_changed(event, layer)
            )

    def _disconnect_events(self) -> None:
        for layer in self._controller.layers:
            layer.groups.events.disconnect(layer._groups_callback)
        self._controller.layers.events.disconnect(self._on_layers_changed)

    def __del__(self) -> None:
        self._disconnect_events()
        for layer in self._controller.layers:
            self._deregister_layer(layer)

    def _on_layers_changed(self, event: Event) -> None:
        if not isinstance(event.sources[0], Sequence):
            return
        layers = event.source
        assert isinstance(layers, Sequence)
        if event.type == "inserted":
            assert isinstance(event.value, Layer)
            self._register_layer(event.value)
        elif event.type == "removed":
            assert isinstance(event.value, Layer)
            self._deregister_layer(event.value)
        elif event.type == "changed" and isinstance(event.index, int):
            pass  # TODO
        elif event.type in ("changed", "reordered"):
            pass  # TODO

    def _on_layer_groups_changed(self, event: Event, layer: Layer) -> None:
        # Events
        # ------
        # changed (key: K, old_value: T, value: T)
        #     emitted when ``key`` is set from ``old_value`` to ``value``
        # adding (key: K)
        #     emitted before an item is added to the dictionary with ``key``
        # added (key: K, value: T)
        #     emitted after ``value`` was added to the dictionary with ``key``
        # removing (key: K)
        #     emitted before ``key`` is removed from the dictionary
        # removed (key: K, value: T)
        #     emitted after ``key`` was removed from the dictionary
        # updated (key, K, value: T)
        #     emitted after ``value`` of ``key`` was changed. Only implemented by
        #     subclasses to give them an option to trigger some update after ``value``
        #     was changed and this class did not register it. This can be useful if
        #     the ``basetype`` is not an evented object.
        # """
        if not isinstance(event.sources[0], Mapping):
            return
        if event.type == "changed":
            assert isinstance(event.key, str)
            assert isinstance(event.value, str)
            assert isinstance(event.old_value, str)
            layer_grouping_widget = self._layer_grouping_widgets[event.key]
            layer_grouping_widget.update_layer(
                layer, event.old_value, new_group=event.value
            )
        elif event.type == "added":
            assert isinstance(event.key, str)
            assert isinstance(event.value, str)
            if event.key in self._layer_grouping_widgets:
                layer_grouping_widget = self._layer_grouping_widgets[event.key]
            else:
                layer_grouping_widget = QLayerGroupingWidget(grouping=event.key)
                self._layer_grouping_widgets[event.key] = layer_grouping_widget
                self._layer_groupings_tab_widget.addTab(
                    layer_grouping_widget, event.key
                )
            layer_grouping_widget.add_layer(layer, group=event.value)
        elif event.type == "removed":
            assert isinstance(event.key, str)
            assert isinstance(event.value, str)
            layer_grouping_widget = self._layer_grouping_widgets[event.key]
            layer_grouping_widget.remove_layer(layer, group=event.value)
            # TODO remove tab if empty
