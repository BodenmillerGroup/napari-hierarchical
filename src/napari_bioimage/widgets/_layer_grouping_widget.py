from typing import Callable, Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListView, QVBoxLayout, QWidget

from napari_bioimage import BioImageController

from ._layer_grouping_model import QLayerGroupingModel


class QLayerGroupingWidget(QWidget):
    def __init__(
        self,
        controller: BioImageController,
        grouping: str,
        close_callback: Callable[["QLayerGroupingWidget"], None],
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self._layer_grouping_view = QListView()
        self._layer_grouping_model = QLayerGroupingModel(
            controller, grouping, lambda: close_callback(self)
        )
        self._layer_grouping_view.setModel(self._layer_grouping_model)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_grouping_view)
        self.setLayout(layout)
