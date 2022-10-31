import pickle
from typing import Any, Iterable, List, NamedTuple, Optional

from napari.utils.events import Event, EventedList
from qtpy.QtCore import QAbstractItemModel, QMimeData, QModelIndex, QObject, Qt

from .._controller import DatasetController
from ..model import Dataset, EventedDatasetChildrenList


class QDatasetTreeModel(QAbstractItemModel):
    class Column(NamedTuple):
        field: str
        title: str
        editable: bool

    COLUMNS = [
        Column("name", "Dataset", True),
    ]

    def __init__(
        self, controller: DatasetController, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if 0 <= column < len(self.COLUMNS):
            if parent.isValid():
                parent_dataset = parent.internalPointer()
                assert isinstance(parent_dataset, Dataset)
                if 0 <= row < len(parent_dataset.children):
                    dataset = parent_dataset.children[row]
                    return self.createIndex(row, column, object=dataset)
            elif 0 <= row < len(self._controller.datasets):
                dataset = self._controller.datasets[row]
                return self.createIndex(row, column, object=dataset)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if index.isValid():
            dataset = index.internalPointer()
            assert isinstance(dataset, Dataset)
            if dataset.parent is not None:
                if dataset.parent.parent is not None:
                    row = dataset.parent.parent.children.index(dataset.parent)
                else:
                    row = self._controller.datasets.index(dataset.parent)
                return self.createIndex(row, 0, object=dataset.parent)
        return QModelIndex()

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        if index.isValid():
            dataset = index.internalPointer()
            assert isinstance(dataset, Dataset)
            return len(dataset.children)
        return len(self._controller.datasets)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid() and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
        ):
            dataset = index.internalPointer()
            assert isinstance(dataset, Dataset)
            assert 0 <= index.column() < len(self.COLUMNS)
            column = self.COLUMNS[index.column()]
            return getattr(dataset, column.field)
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            dataset = index.internalPointer()
            assert isinstance(dataset, Dataset)
            assert 0 <= index.column() < len(self.COLUMNS)
            column = self.COLUMNS[index.column()]
            setattr(dataset, column.field, value)
            return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.isValid():
            assert flags & Qt.ItemFlag.ItemIsEnabled
            assert flags & Qt.ItemFlag.ItemIsSelectable
            assert 0 <= index.column() < len(self.COLUMNS)
            column = self.COLUMNS[index.column()]
            if column.editable:
                flags |= Qt.ItemFlag.ItemIsEditable
            flags |= Qt.ItemFlag.ItemIsDragEnabled
        flags |= Qt.ItemFlag.ItemIsDropEnabled
        return flags

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and 0 <= section < len(self.COLUMNS):
            column = self.COLUMNS[section]
            return column.title
        return None

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if parent.isValid():
            parent_dataset = parent.internalPointer()
            assert isinstance(parent_dataset, Dataset)
            datasets = parent_dataset.children
        else:
            parent_dataset = None
            datasets = self._controller.datasets
        if 0 <= row <= len(datasets) and count > 0:
            for i in range(row, row + count):
                dataset = Dataset(name="New Dataset", parent=parent_dataset)
                datasets.insert(i, dataset)
            return True
        return False

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if parent.isValid():
            parent_dataset = parent.internalPointer()
            assert isinstance(parent_dataset, Dataset)
            datasets = parent_dataset.children
        else:
            datasets = self._controller.datasets
        if 0 <= row < row + count <= len(datasets) and count > 0:
            for _ in range(count):
                datasets.pop(row)
            return True
        return False

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeTypes(self) -> List[str]:
        mime_types = super().mimeTypes()
        mime_types.append("x-napari-dataset-dataset")
        mime_types.append("x-napari-dataset-layer")
        return mime_types

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        data = super().mimeData(indexes)
        indices_stacks = []
        for index in indexes:
            indices_stack = []
            while index.isValid():
                indices_stack.append(index.row())
                index = index.parent()
            indices_stacks.append(indices_stack)
        data.setData("x-napari-dataset-dataset", pickle.dumps(indices_stacks))
        return data

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if action not in (Qt.DropAction.CopyAction, Qt.DropAction.MoveAction):
            return False
        if data.hasFormat("x-napari-dataset-dataset"):
            indices_stacks = pickle.loads(data.data("x-napari-dataset-dataset").data())
            assert isinstance(indices_stacks, list) and len(indices_stacks) > 0
            if parent.isValid():
                parent_dataset = parent.internalPointer()
                assert isinstance(parent_dataset, Dataset)
                datasets = parent_dataset.children
            else:
                parent_dataset = None
                datasets = self._controller.datasets
            if row == -1 and column == -1:
                row = len(datasets)
            assert 0 <= row <= len(datasets)
            n = 0
            while len(indices_stacks) > 0:
                indices_stack = indices_stacks.pop(0)
                assert isinstance(indices_stack, list) and len(indices_stack) > 0
                source_datasets = self._controller.datasets
                source_row = indices_stack.pop()
                assert isinstance(source_row, int)
                while len(indices_stack) > 0:
                    source_datasets = source_datasets[source_row].children
                    source_row = indices_stack.pop()
                    assert isinstance(source_row, int)
                dataset = source_datasets[source_row].copy(deep=True)
                datasets.insert(row + n, dataset)
                n += 1
            return True
        if data.hasFormat("x-napari-dataset-layer"):
            pass  # TODO
        return False

    def _connect_events(self) -> None:
        for dataset in self._controller.datasets:
            self._connect_dataset_events(dataset)
        self._controller.datasets.events.connect(self._on_datasets_event)

    def _disconnect_events(self) -> None:
        self._controller.datasets.events.disconnect(self._on_datasets_event)
        for dataset in self._controller.datasets:
            self._disconnect_dataset_events(dataset)

    def _connect_dataset_events(self, dataset: Dataset) -> None:
        for child in dataset.children:
            self._connect_dataset_events(child)
        dataset.children.events.connect(self._on_datasets_event)
        dataset.events.connect(self._on_dataset_event)

    def _disconnect_dataset_events(self, dataset: Dataset) -> None:
        dataset.events.disconnect(self._on_dataset_event)
        dataset.children.events.disconnect(self._on_datasets_event)
        for child in dataset.children:
            self._disconnect_dataset_events(child)

    def _on_datasets_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        assert isinstance(event.source, EventedList)
        datasets = event.source
        if isinstance(datasets, EventedDatasetChildrenList):
            parent_dataset = datasets.dataset
        else:
            parent_dataset = None

        def get_parent():
            if parent_dataset is not None:
                if parent_dataset.parent is not None:
                    parent_row = parent_dataset.parent.children.index(parent_dataset)
                else:
                    parent_row = self._controller.datasets.index(parent_dataset)
                return self.createIndex(parent_row, 0, object=parent_dataset)
            return QModelIndex()

        if event.type == "inserting":
            assert isinstance(event.index, int) and 0 <= event.index <= len(datasets)
            self.beginInsertRows(get_parent(), event.index, event.index)
        elif event.type == "inserted":
            self.endInsertRows()
            assert isinstance(event.value, Dataset)
            self._connect_dataset_events(event.value)
        elif event.type == "removing":
            assert isinstance(event.index, int) and 0 <= event.index < len(datasets)
            self._disconnect_dataset_events(datasets[event.index])
            self.beginRemoveRows(get_parent(), event.index, event.index)
        elif event.type == "removed":
            self.endRemoveRows()
        elif event.type == "moving":
            assert isinstance(event.index, int) and 0 <= event.index < len(datasets)
            assert (
                isinstance(event.new_index, int)
                and 0 <= event.new_index <= len(datasets)
                and event.new_index != event.index
            )
            parent = get_parent()
            self.beginMoveRows(
                parent, event.index, event.index, parent, event.new_index
            )
        elif event.type == "moved":
            self.endMoveRows()
        elif event.type == "changed" and isinstance(event.index, int):
            assert 0 <= event.index < len(datasets)
            left_index = self.createIndex(event.index, 0, object=datasets[event.index])
            right_index = self.createIndex(
                event.index, len(self.COLUMNS) - 1, object=datasets[event.index]
            )
            self.dataChanged.emit(left_index, right_index)
        elif event.type in ("changed", "reordered"):
            top_left_index = self.createIndex(0, 0, object=datasets[0])
            bottom_right_index = self.createIndex(
                len(datasets) - 1, len(self.COLUMNS) - 1, object=datasets[-1]
            )
            self.dataChanged.emit(top_left_index, bottom_right_index)

    def _on_dataset_event(self, event: Event) -> None:
        assert isinstance(event.source, Dataset)
        dataset = event.source
        column_index = next(
            (i for i, c in enumerate(self.COLUMNS) if c.field == event.type), None
        )
        if column_index is not None:
            if dataset.parent is not None:
                row = dataset.parent.children.index(dataset)
            else:
                row = self._controller.datasets.index(dataset)
            index = self.createIndex(row, column_index, object=dataset)
            self.dataChanged.emit(index, index)
