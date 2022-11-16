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
from ..model import Array
from ._flat_array_groupings_tab_widget import QFlatArrayGroupingsTabWidget


# TODO styling (buttons)
class QArraysWidget(QWidget):
    def __init__(
        self,
        napari_viewer: Viewer,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        if controller.viewer != napari_viewer:
            controller.register_viewer(napari_viewer)
        self._new_points_array_push_button = QPushButton("+ Points")
        self._new_points_array_push_button.clicked.connect(
            self._on_new_points_array_push_button_clicked
        )
        self._new_shapes_array_push_button = QPushButton("+ Shapes")
        self._new_shapes_array_push_button.clicked.connect(
            self._on_new_shapes_array_push_button_clicked
        )
        self._new_labels_array_push_button = QPushButton("+ Labels")
        self._new_labels_array_push_button.clicked.connect(
            self._on_new_labels_array_push_button_clicked
        )
        self._delete_array_push_button = QPushButton("Delete")
        self._delete_array_push_button.clicked.connect(
            self._on_delete_array_push_button_clicked
        )
        self._array_tool_bar = QToolBar("Arrays")
        self._array_tool_bar.addWidget(QLabel("Arrays"))
        array_tool_bar_spacer = QWidget()
        array_tool_bar_spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._array_tool_bar.addWidget(array_tool_bar_spacer)
        self._array_tool_bar.addWidget(self._new_points_array_push_button)
        self._array_tool_bar.addWidget(self._new_shapes_array_push_button)
        self._array_tool_bar.addWidget(self._new_labels_array_push_button)
        self._array_tool_bar.addWidget(self._delete_array_push_button)
        self._flat_array_groupings_tab_widget = QFlatArrayGroupingsTabWidget(controller)
        self._init_layout()
        self._connect_events()
        self._check_new_array_push_buttons_enabled()
        self._check_delete_array_push_button_enabled()

    def _init_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._array_tool_bar)
        layout.addWidget(self._flat_array_groupings_tab_widget)
        self.setLayout(layout)

    def _connect_events(self) -> None:
        controller.selected_groups.events.connect(self._on_selected_groups_event)
        controller.current_arrays.selection.events.changed.connect(
            self._on_current_arrays_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        controller.selected_groups.events.disconnect(self._on_selected_groups_event)
        controller.current_arrays.selection.events.changed.disconnect(
            self._on_current_arrays_selection_changed_event
        )

    def _on_selected_groups_event(self, event: Event) -> None:
        self._check_new_array_push_buttons_enabled()

    def _on_current_arrays_selection_changed_event(self, event: Event) -> None:
        self._check_delete_array_push_button_enabled()

    def _on_new_points_array_push_button_clicked(self, checked: bool = False) -> None:
        assert controller.viewer is not None
        assert len(controller.selected_groups) == 1
        group = controller.selected_groups[0]
        layer = controller.viewer.add_points()
        array = Array(name=layer.name, layer=layer, loaded_layer=layer)
        group.arrays.append(array)

    def _on_new_shapes_array_push_button_clicked(self, checked: bool = False) -> None:
        assert controller.viewer is not None
        assert len(controller.selected_groups) == 1
        group = controller.selected_groups[0]
        layer = controller.viewer.add_shapes()
        array = Array(name=layer.name, layer=layer, loaded_layer=layer)
        group.arrays.append(array)

    def _on_new_labels_array_push_button_clicked(self, checked: bool = False) -> None:
        assert controller.viewer is not None
        assert len(controller.selected_groups) == 1
        group = controller.selected_groups[0]
        layer = controller.viewer.add_labels([])
        array = Array(name=layer.name, layer=layer, loaded_layer=layer)
        group.arrays.append(array)

    def _on_delete_array_push_button_clicked(self, checked: bool = False) -> None:
        arrays = list(controller.current_arrays.selection)
        controller.current_arrays.selection.clear()
        for array in arrays:
            array.parent.arrays.remove(array)

    def _check_new_array_push_buttons_enabled(self) -> None:
        self._new_points_array_push_button.setEnabled(
            len(controller.selected_groups) == 1
        )
        self._new_shapes_array_push_button.setEnabled(
            len(controller.selected_groups) == 1
        )
        self._new_labels_array_push_button.setEnabled(
            len(controller.selected_groups) == 1
        )

    def _check_delete_array_push_button_enabled(self) -> None:
        self._delete_array_push_button.setEnabled(
            len(controller.current_arrays.selection) > 0
        )
