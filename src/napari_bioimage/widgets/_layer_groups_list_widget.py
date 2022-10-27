from typing import Callable, Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QListView, QVBoxLayout, QWidget

from napari_bioimage import BioImageController

from ._layer_groups_list_model import QLayerGroupsListModel


class QLayerGroupsListWidget(QWidget):
    def __init__(
        self,
        controller: BioImageController,
        grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self._layer_groups_list_view = QListView()
        self._layer_groups_list_model = QLayerGroupsListModel(
            controller, grouping=grouping, close_callback=close_callback
        )
        self._layer_groups_list_view.setModel(self._layer_groups_list_model)
        # self._layer_groups_list_view.selectionModel().selectionChanged.connect(
        #     self._on_layer_groups_list_view_selection_changed
        # )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._layer_groups_list_view)
        self.setLayout(layout)

    # def _on_layer_groups_list_view_selection_changed(
    #     self, selected: QItemSelection, deselected: QItemSelection
    # ) -> None:
    #     self._controller.layers.selection.clear()
    #     for index in self._layer_groups_list_view.selectedIndexes():
    #         group = self._layer_groups_list_model.groups[index.row()]
    #         for layer in self._layer_groups_list_model.group_layers[group]:
    #             self._controller.layers.selection.add(layer)
