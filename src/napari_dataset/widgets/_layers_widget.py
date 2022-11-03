from typing import Optional, Union

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
from ._layer_groupings_tab_widget import QLayerGroupingsTabWidget


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
        self._add_points_layer_push_button = QPushButton("+ Points")
        self._add_shapes_layer_push_button = QPushButton("+ Shapes")
        self._add_labels_layer_push_button = QPushButton("+ Labels")
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._layer_tool_bar.addWidget(QLabel("Layers"))
        self._layer_tool_bar.addWidget(spacer)
        self._layer_tool_bar.addWidget(self._add_points_layer_push_button)
        self._layer_tool_bar.addWidget(self._add_shapes_layer_push_button)
        self._layer_tool_bar.addWidget(self._add_labels_layer_push_button)
        self._layer_groupings_tab_widget = QLayerGroupingsTabWidget(controller)
        self._init_layout()

    def _init_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_tool_bar)
        layout.addWidget(self._layer_groupings_tab_widget)
        self.setLayout(layout)
