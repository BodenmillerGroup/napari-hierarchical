from typing import Optional, Union

from napari.viewer import Viewer
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QVBoxLayout, QWidget

from .._controller import controller
from ._image_tree_widget import QImageTreeWidget


class QImagesWidget(QWidget):
    def __init__(
        self,
        napari_viewer: Viewer,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        if controller.viewer != napari_viewer:
            controller.register_viewer(napari_viewer)
        self._image_tree_widget = QImageTreeWidget(controller)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._image_tree_widget)
        self.setLayout(layout)
