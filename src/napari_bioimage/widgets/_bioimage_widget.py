from typing import Optional, Union

from napari.viewer import Viewer
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSplitter, QVBoxLayout, QWidget

from .._controller import controller
from ._image_tree_widget import QImageTreeWidget
from ._layer_groups_widget import QLayerGroupsWidget
from ._layer_properties_widget import QLayerPropertiesWidget


class QBioImageWidget(QWidget):
    def __init__(
        self,
        napari_viewer: Viewer,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        if controller.viewer != napari_viewer:
            controller.register_viewer(napari_viewer)
        controller.register_widget(self)
        self._image_tree_widget = QImageTreeWidget(controller)
        self._layer_groups_widget = QLayerGroupsWidget(controller)
        self._layer_properties_widget = QLayerPropertiesWidget(controller)
        self.setupUI()

    def setupUI(self) -> None:
        layout = QVBoxLayout()
        splitter = QSplitter(orientation=Qt.Orientation.Vertical)
        splitter.addWidget(self._image_tree_widget)
        splitter.addWidget(self._layer_groups_widget)
        splitter.addWidget(self._layer_properties_widget)
        layout.addWidget(splitter)
        self.setLayout(layout)
