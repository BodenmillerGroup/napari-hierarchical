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
from ._dataset_tree_view import QDatasetTreeView


class QDatasetsWidget(QWidget):
    def __init__(
        self,
        napari_viewer: Viewer,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        if controller.viewer != napari_viewer:
            controller.register_viewer(napari_viewer)
        self._dataset_tool_bar = QToolBar("Datasets")
        self._open_dataset_push_button = QPushButton("Open")
        self._create_dataset_push_button = QPushButton("Create")
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._dataset_tool_bar.addWidget(QLabel("Datasets"))
        self._dataset_tool_bar.addWidget(spacer)
        self._dataset_tool_bar.addWidget(self._open_dataset_push_button)
        self._dataset_tool_bar.addWidget(self._create_dataset_push_button)
        self._dataset_tree_view = QDatasetTreeView(controller)
        self._init_layout()

    def _init_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._dataset_tool_bar)
        layout.addWidget(self._dataset_tree_view)
        self.setLayout(layout)
