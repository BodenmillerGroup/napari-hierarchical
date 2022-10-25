from typing import Any, List, Optional

from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt

from .._controller import BioImageController
from ..model import Layer


class LayerGroupingModel(QAbstractItemModel):
    def __init__(
        self,
        controller: BioImageController,
        grouping: Optional[str] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._grouping = grouping
        self._group_layers: dict[str, List[Layer]] = {}

    def __del__(self) -> None:
        pass

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        return super().index(row, column, parent)

    def parent(self, index: QModelIndex) -> QModelIndex:
        return super().parent(index)

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
