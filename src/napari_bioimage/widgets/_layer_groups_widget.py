from typing import Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from .._controller import BioImageController


class QLayerGroupsWidget(QWidget):
    def __init__(
        self,
        controller: BioImageController,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self._layer_groups_tab_widget = QTabWidget()
        self.setupUI()

    def setupUI(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_groups_tab_widget)
        self.setLayout(layout)
