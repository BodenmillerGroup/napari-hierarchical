from typing import Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTreeView, QVBoxLayout, QWidget

from .._controller import NapariDatasetController
from ._dataset_tree_model import QDatasetTreeModel


class QDatasetTreeWidget(QWidget):
    def __init__(
        self,
        controller: NapariDatasetController,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._controller = controller
        self._image_tree_view = QTreeView()
        self._image_tree_model = QDatasetTreeModel(controller)
        self._image_tree_view.setModel(self._image_tree_model)
        # self._image_tree_view.selectionModel().selectionChanged.connect(
        #     self._on_image_tree_view_selection_changed
        # )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        self._image_tree_view.setHeaderHidden(True)
        self._image_tree_view.setSelectionMode(
            QTreeView.SelectionMode.ExtendedSelection
        )
        self._image_tree_view.setDragEnabled(True)
        self._image_tree_view.setAcceptDrops(True)
        self._image_tree_view.setDropIndicatorShown(True)
        self._image_tree_view.setDragDropMode(QTreeView.DragDropMode.InternalMove)
        layout.addWidget(self._image_tree_view)
        self.setLayout(layout)

    # def _on_image_tree_view_selection_changed(
    #     self, selected: QItemSelection, deselected: QItemSelection
    # ) -> None:
    #     self._controller.images.selection.clear()
    #     self._controller.layers.selection.clear()
    #     for index in self._image_tree_view.selectedIndexes():
    #         image = index.internalPointer()
    #         assert isinstance(image, Image)
    #         self._controller.images.selection.add(image)
    #         for layer in image.get_layers(recursive=True):
    #             self._controller.layers.selection.add(layer)
