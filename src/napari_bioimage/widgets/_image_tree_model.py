from typing import Any, Optional

from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt


class QImageTreeModel(QAbstractItemModel):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        return super().index(row, column, parent)

    def parent(child: QModelIndex) -> QModelIndex:
        return super().parent(child)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return super().rowCount(parent)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return super().columnCount(parent)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        return super().data(index, role)

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        return super().setData(index, value, role)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        return super().headerData(section, orientation, role)

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        return super().insertRows(row, count, parent)

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        return super().removeRows(row, count, parent)
