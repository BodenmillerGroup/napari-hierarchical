from typing import Any, Optional

from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt

from .._controller import BioImageController
from ..model import Image, ImageGroup


class QImageTreeModel(QAbstractItemModel):
    def __init__(
        self, controller: BioImageController, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if self.hasIndex(row, column, parent=parent):
            if parent.isValid():
                parent_image_group = parent.internalPointer()
                assert isinstance(parent_image_group, ImageGroup)
                if 0 <= row < len(parent_image_group.children):
                    image = parent_image_group.children[row]
                    return self.createIndex(row, column, object=image)
            elif 0 <= row < len(self._controller.images):
                image = self._controller.images[row]
                return self.createIndex(row, column, object=image)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if index.isValid():
            image = index.internalPointer()
            assert isinstance(image, Image)
            if image.parent is not None:
                if image.parent.parent is not None:
                    row = image.parent.parent.children.index(image.parent)
                else:
                    row = self._controller.images.index(image.parent)
                return self.createIndex(row, 0, object=image.parent)
        return QModelIndex()

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        if index.isValid():
            image = index.internalPointer()
            if isinstance(image, ImageGroup):
                return len(image.children)
            return 0
        return len(self._controller.images)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid():
            image = index.internalPointer()
            assert isinstance(image, Image)
            if role == Qt.ItemDataRole.DisplayRole:
                return image.name
        return None

    # def setData(
    #     self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    # ) -> bool:
    #     return super().setData(index, value, role)

    # def flags(self, index: QModelIndex) -> Qt.ItemFlags:
    #     return super().flags(index)

    # def headerData(
    #     self,
    #     section: int,
    #     orientation: Qt.Orientation,
    #     role: int = Qt.ItemDataRole.DisplayRole,
    # ) -> Any:
    #     return super().headerData(section, orientation, role)

    # def insertRows(
    #     self, row: int, count: int, parent: QModelIndex = QModelIndex()
    # ) -> bool:
    #     return super().insertRows(row, count, parent)

    # def removeRows(
    #     self, row: int, count: int, parent: QModelIndex = QModelIndex()
    # ) -> bool:
    #     return super().removeRows(row, count, parent)
