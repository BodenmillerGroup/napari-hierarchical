from typing import Optional, Union

from napari.viewer import Viewer
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSplitter, QVBoxLayout, QWidget

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
        self._viewer = napari_viewer
        self._image_tree_widget = QImageTreeWidget()
        self._layer_groups_widget = QLayerGroupsWidget()
        self._layer_properties_widget = QLayerPropertiesWidget()
        self.setupUI()

    def setupUI(self) -> None:
        layout = QVBoxLayout()
        splitter = QSplitter(orientation=Qt.Orientation.Vertical)
        splitter.addWidget(self._image_tree_widget)
        splitter.addWidget(self._layer_groups_widget)
        splitter.addWidget(self._layer_properties_widget)
        layout.addWidget(splitter)
        self.setLayout(layout)
