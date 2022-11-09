from typing import Optional, Union

from napari.utils.events import Event
from napari.viewer import Viewer
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .._controller import controller
from ..model import Layer
from ._layer_groups_widget import QLayerGroupsWidget


class QLayersWidget(QWidget):
    def __init__(
        self,
        napari_viewer: Viewer,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        if controller.viewer != napari_viewer:
            controller.register_viewer(napari_viewer)
        self._layer_tool_bar = QToolBar("Layers")
        self._new_points_layer_push_button = QPushButton("+ Points")
        self._new_points_layer_push_button.clicked.connect(
            self._on_new_points_layer_push_button_clicked
        )
        self._new_points_layer_push_button.setEnabled(
            len(controller.selected_datasets) == 1
        )
        self._new_shapes_layer_push_button = QPushButton("+ Shapes")
        self._new_shapes_layer_push_button.clicked.connect(
            self._on_new_shapes_layer_push_button_clicked
        )
        self._new_shapes_layer_push_button.setEnabled(
            len(controller.selected_datasets) == 1
        )
        self._new_labels_layer_push_button = QPushButton("+ Labels")
        self._new_labels_layer_push_button.clicked.connect(
            self._on_new_labels_layer_push_button_clicked
        )
        self._new_labels_layer_push_button.setEnabled(
            len(controller.selected_datasets) == 1
        )
        self._delete_layer_push_button = QPushButton("Delete")
        self._delete_layer_push_button.clicked.connect(
            self._on_delete_layer_push_button_clicked
        )
        self._delete_layer_push_button.setEnabled(
            len(controller.current_layers.selection) > 0
        )
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._layer_tool_bar.addWidget(QLabel("Layers"))
        self._layer_tool_bar.addWidget(spacer)
        self._layer_tool_bar.addWidget(self._new_points_layer_push_button)
        self._layer_tool_bar.addWidget(self._new_shapes_layer_push_button)
        self._layer_tool_bar.addWidget(self._new_labels_layer_push_button)
        self._layer_tool_bar.addWidget(self._delete_layer_push_button)
        self._layer_groups_widget = QLayerGroupsWidget(controller)
        self._init_layout()
        self._connect_events()

    def _init_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_tool_bar)
        layout.addWidget(self._layer_groups_widget)
        self.setLayout(layout)

    def _connect_events(self) -> None:
        controller.selected_datasets.events.connect(self._on_selected_datasets_event)
        controller.current_layers.selection.events.changed.connect(
            self._on_current_layers_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        controller.selected_datasets.events.disconnect(self._on_selected_datasets_event)
        controller.current_layers.selection.events.changed.disconnect(
            self._on_current_layers_selection_changed_event
        )

    def _on_selected_datasets_event(self, event: Event) -> None:
        self._new_points_layer_push_button.setEnabled(
            len(controller.selected_datasets) == 1
        )
        self._new_shapes_layer_push_button.setEnabled(
            len(controller.selected_datasets) == 1
        )
        self._new_labels_layer_push_button.setEnabled(
            len(controller.selected_datasets) == 1
        )

    def _on_current_layers_selection_changed_event(self, event: Event) -> None:
        self._delete_layer_push_button.setEnabled(
            len(controller.current_layers.selection) > 0
        )

    def _on_new_points_layer_push_button_clicked(self, checked: bool = False) -> None:
        assert controller.viewer is not None
        assert len(controller.selected_datasets) == 1
        dataset = controller.selected_datasets[0]
        napari_layer = controller.viewer.add_points()
        layer = Layer(
            name=napari_layer.name,
            napari_layer=napari_layer,
            loaded_napari_layer=napari_layer,
        )
        dataset.layers.append(layer)
        # self._layer_group_table_views_tab_widget.setCurrentIndex(0)
        # TODO select layer group

    def _on_new_shapes_layer_push_button_clicked(self, checked: bool = False) -> None:
        assert controller.viewer is not None
        assert len(controller.selected_datasets) == 1
        dataset = controller.selected_datasets[0]
        napari_layer = controller.viewer.add_shapes()
        layer = Layer(
            name=napari_layer.name,
            napari_layer=napari_layer,
            loaded_napari_layer=napari_layer,
        )
        dataset.layers.append(layer)
        # self._layer_group_table_views_tab_widget.setCurrentIndex(0)
        # TODO select layer group

    def _on_new_labels_layer_push_button_clicked(self, checked: bool = False) -> None:
        assert controller.viewer is not None
        assert len(controller.selected_datasets) == 1
        dataset = controller.selected_datasets[0]
        napari_layer = controller.viewer.add_labels()
        layer = Layer(
            name=napari_layer.name,
            napari_layer=napari_layer,
            loaded_napari_layer=napari_layer,
        )
        dataset.layers.append(layer)
        # self._layer_group_table_views_tab_widget.setCurrentIndex(0)
        # TODO select layer group

    def _on_delete_layer_push_button_clicked(self, checked: bool = False) -> None:
        layers = list(controller.current_layers.selection)
        controller.current_layers.selection.clear()
        for layer in layers:
            layer.parent.layers.remove(layer)
