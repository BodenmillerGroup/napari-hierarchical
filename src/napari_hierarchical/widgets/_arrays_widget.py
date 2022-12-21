import logging
from typing import Optional, Union

import numpy as np
from napari.utils.events import Event, EventedList
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
from ._flat_groupings_tab_widget import QFlatGroupingsTabWidget

logger = logging.getLogger(__name__)


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
        self._flat_groupings_tab_widget = QFlatGroupingsTabWidget(controller)
        self._init_layout()
        self._connect_events()
        self._update_new_array_push_buttons_enabled()
        self._update_delete_array_push_button_enabled()

    def __del__(self) -> None:
        self._disconnect_events()

    def _init_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._array_tool_bar)
        layout.addWidget(self._flat_groupings_tab_widget)
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
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type in ("inserted", "removed", "changed"):
            logger.debug(f"event={event.type}")
            self._update_new_array_push_buttons_enabled()

    def _on_current_arrays_selection_changed_event(self, event: Event) -> None:
        logger.debug("")
        self._update_delete_array_push_button_enabled()

    def _on_new_points_array_push_button_clicked(self, checked: bool = False) -> None:
        logger.debug(f"checked={checked}")
        assert controller.viewer is not None
        assert len(controller.selected_groups) == 1
        group = controller.selected_groups[0]
        layer = controller.viewer.add_points(
            ndim=max(controller.viewer.dims.ndim, 2),
            scale=controller.viewer.layers.extent.step,
        )
        array = Array(name=layer.name, layer=layer)
        group.arrays.append(array)

    def _on_new_shapes_array_push_button_clicked(self, checked: bool = False) -> None:
        logger.debug(f"checked={checked}")
        assert controller.viewer is not None
        assert len(controller.selected_groups) == 1
        group = controller.selected_groups[0]
        layer = controller.viewer.add_shapes(
            ndim=max(controller.viewer.dims.ndim, 2),
            scale=controller.viewer.layers.extent.step,
        )
        array = Array(name=layer.name, layer=layer)
        group.arrays.append(array)

    def _on_new_labels_array_push_button_clicked(self, checked: bool = False) -> None:
        logger.debug(f"checked={checked}")
        assert controller.viewer is not None
        assert len(controller.selected_groups) == 1
        group = controller.selected_groups[0]
        layer = controller.viewer.add_labels(
            np.zeros(
                [
                    np.round(s / sc).astype("int") if s > 0 else 1
                    for s, sc in zip(
                        controller.viewer.layers.extent.world[1]
                        - controller.viewer.layers.extent.world[0],
                        controller.viewer.layers.extent.step,
                    )
                ],
                dtype=int,
            ),
            translate=np.array(
                controller.viewer.layers.extent.world[0]
                + 0.5 * controller.viewer.layers.extent.step
            ),
            scale=controller.viewer.layers.extent.step,
        )  # copied from ViewerModel._new_labels()
        array = Array(name=layer.name, layer=layer)
        group.arrays.append(array)

    def _on_delete_array_push_button_clicked(self, checked: bool = False) -> None:
        logger.debug(f"checked={checked}")
        arrays = list(controller.current_arrays.selection)
        controller.current_arrays.selection.clear()
        for array in arrays:
            if array.loaded:
                controller.unload_array(array)
            assert array.layer is None
            assert array.parent is not None
            array.parent.arrays.remove(array)

    def _update_new_array_push_buttons_enabled(self) -> None:
        enabled = len(controller.selected_groups) == 1
        logger.debug(f"enabled={enabled}")
        self._new_points_array_push_button.setEnabled(enabled)
        self._new_shapes_array_push_button.setEnabled(enabled)
        self._new_labels_array_push_button.setEnabled(enabled)

    def _update_delete_array_push_button_enabled(self) -> None:
        enabled = len(controller.current_arrays.selection) > 0
        logger.debug(f"enabled={enabled}")
        self._delete_array_push_button.setEnabled(enabled)
