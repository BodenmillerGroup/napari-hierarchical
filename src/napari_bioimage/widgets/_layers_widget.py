from typing import Optional, Union

from napari.viewer import Viewer
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QVBoxLayout, QWidget

from .._controller import controller
from ._layer_groupings_widget import QLayerGroupingsWidget


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
        self._layer_groupings_widget = QLayerGroupingsWidget(controller)
        self._setup_user_interface()

    def _setup_user_interface(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_groupings_widget)
        self.setLayout(layout)
