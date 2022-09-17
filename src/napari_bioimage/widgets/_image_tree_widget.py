from typing import Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTreeView, QVBoxLayout, QWidget

from ._image_tree_model import QImageTreeModel


class QImageTreeWidget(QWidget):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._image_tree_view = QTreeView()
        self._image_tree_model = QImageTreeModel()
        self._image_tree_view.setModel(self._image_tree_model)
        self.setupUI()

    def setupUI(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._image_tree_model)
        self.setLayout(layout)
