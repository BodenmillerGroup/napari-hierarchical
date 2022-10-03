from typing import Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QVBoxLayout, QWidget

from .._controller import BioImageController


class QLayerPropertiesWidget(QWidget):
    def __init__(
        self,
        controller: BioImageController,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self.setupUI()

    def setupUI(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)
