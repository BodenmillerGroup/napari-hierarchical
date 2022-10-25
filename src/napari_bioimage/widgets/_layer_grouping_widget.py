from typing import Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget

from ..model import Layer


class QLayerGroupingWidget(QWidget):
    def __init__(
        self,
        grouping: Optional[str] = None,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._grouping = grouping
        self._setup_ui()

    def add_layer(self, layer: Layer) -> None:
        pass  # TODO

    def remove_layer(self, layer: Layer) -> None:
        pass  # TODO

    def _setup_ui(self) -> None:
        pass  # TODO
