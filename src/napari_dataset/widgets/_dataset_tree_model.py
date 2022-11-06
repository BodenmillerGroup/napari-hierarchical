import pickle
from typing import Any, Iterable, List, NamedTuple, Optional

from napari.utils.events import Event, EventedList
from qtpy.QtCore import QAbstractItemModel, QMimeData, QModelIndex, QObject, Qt

from .._controller import DatasetController
from ..model import Dataset
from ..utils.parent_aware import NestedParentAwareEventedModelList


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
            parent_dataset = dataset.get_parent()
            if parent_dataset is not None:
                return self.create_dataset_index(parent_dataset)
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
                dataset = Dataset(name="New Dataset")
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
        mime_types.append("x-napari-dataset")
        return mime_types

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        data = super().mimeData(indexes)
        indices_stacks = []
        for index in indexes:
            indices_stack = []
            dataset = index.internalPointer()
            assert isinstance(dataset, Dataset)
            parent_dataset = dataset.get_parent()
            while parent_dataset is not None:
                indices_stack.append(parent_dataset.children.index(dataset))
                dataset = parent_dataset
                parent_dataset = dataset.get_parent()
            indices_stack.append(self._controller.datasets.index(dataset))
            indices_stacks.append(indices_stack)
        data.setData("x-napari-dataset", pickle.dumps(indices_stacks))
        return data

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if data.hasFormat("x-napari-dataset") and action in (
            Qt.DropAction.CopyAction,
            Qt.DropAction.MoveAction,
        ):
            indices_stacks = pickle.loads(data.data("x-napari-dataset").data())
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
                source_dataset = source_datasets[source_row]
                dataset = source_dataset.copy(deep=True)
                datasets.insert(row + n, dataset)
                n += 1
            return True
        return False

    def create_dataset_index(self, dataset: Dataset, column: int = 0) -> QModelIndex:
        parent_dataset = dataset.get_parent()
        if parent_dataset is not None:
            parent_datasets = parent_dataset.children
        else:
            parent_datasets = self._controller.datasets
        row = parent_datasets.index(dataset)
        return self.createIndex(row, column, object=dataset)

    def _connect_events(self) -> None:
        self._controller.datasets.events.connect(self._on_datasets_event)
        for dataset in self._controller.datasets:
            self._connect_dataset_events(dataset)

    def _disconnect_events(self) -> None:
        for dataset in self._controller.datasets:
            self._disconnect_dataset_events(dataset)
        self._controller.datasets.events.disconnect(self._on_datasets_event)

    def _connect_dataset_events(self, dataset: Dataset) -> None:
        dataset.nested_event.connect(self._on_dataset_nested_event)
        dataset.nested_list_event.connect(self._on_dataset_nested_list_event)

    def _disconnect_dataset_events(self, dataset: Dataset) -> None:
        dataset.nested_event.disconnect(self._on_dataset_nested_event)
        dataset.nested_list_event.disconnect(self._on_dataset_nested_list_event)

    def _on_datasets_event(self, event: Event) -> None:
        self._process_datasets_event(event, connect=True)

    def _on_dataset_nested_list_event(self, event: Event) -> None:
        assert isinstance(event.source_event, Event)
        datasets = event.source_event.source
        assert isinstance(datasets, NestedParentAwareEventedModelList)
        parent_dataset = datasets.get_parent()
        assert isinstance(parent_dataset, Dataset)
        if datasets == parent_dataset.children:
            self._process_datasets_event(event.source_event)

    def _process_datasets_event(self, event: Event, connect: bool = False) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        datasets = event.source
        assert isinstance(datasets, EventedList)

        def get_parent_index() -> QModelIndex:
            if isinstance(datasets, NestedParentAwareEventedModelList):
                parent_dataset = datasets.get_parent()
                assert isinstance(parent_dataset, Dataset)
                return self.create_dataset_index(parent_dataset)
            return QModelIndex()

        if event.type == "inserting":
            assert isinstance(event.index, int) and 0 <= event.index <= len(datasets)
            self.beginInsertRows(get_parent_index(), event.index, event.index)
        elif event.type == "inserted":
            self.endInsertRows()
            if connect:
                assert isinstance(event.value, Dataset)
                self._connect_dataset_events(event.value)
        elif event.type == "removing":
            assert isinstance(event.index, int) and 0 <= event.index < len(datasets)
            if connect:
                dataset = datasets[event.index]
                assert isinstance(dataset, Dataset)
                self._disconnect_dataset_events(dataset)
            self.beginRemoveRows(get_parent_index(), event.index, event.index)
        elif event.type == "removed":
            self.endRemoveRows()
        elif event.type == "moving":
            assert isinstance(event.index, int) and 0 <= event.index < len(datasets)
            assert (
                isinstance(event.new_index, int)
                and 0 <= event.new_index <= len(datasets)
                and event.new_index != event.index
            )
            parent_index = get_parent_index()
            self.beginMoveRows(
                parent_index, event.index, event.index, parent_index, event.new_index
            )
        elif event.type == "moved":
            self.endMoveRows()
        elif event.type == "changed" and isinstance(event.index, int):
            assert 0 <= event.index < len(datasets)
            if connect:
                assert isinstance(event.old_value, Dataset)
                self._disconnect_dataset_events(event.old_value)
                assert isinstance(event.value, Dataset)
                self._connect_dataset_events(event.value)
            left_index = self.createIndex(event.index, 0, object=datasets[event.index])
            right_index = self.createIndex(
                event.index, len(self.COLUMNS) - 1, object=datasets[event.index]
            )
            self.dataChanged.emit(left_index, right_index)
        elif event.type == "changed":
            if connect:
                assert isinstance(event.old_value, List)
                for old_dataset in event.old_value:
                    assert isinstance(old_dataset, Dataset)
                    self._disconnect_dataset_events(old_dataset)
                assert isinstance(event.value, List)
                for dataset in event.value:
                    assert isinstance(dataset, Dataset)
                    self._connect_dataset_events(dataset)
            top_left_index = self.createIndex(0, 0, object=datasets[0])
            bottom_right_index = self.createIndex(
                len(datasets) - 1, len(self.COLUMNS) - 1, object=datasets[-1]
            )
            self.dataChanged.emit(top_left_index, bottom_right_index)
        elif event.type == "reordered":
            top_left_index = self.createIndex(0, 0, object=datasets[0])
            bottom_right_index = self.createIndex(
                len(datasets) - 1, len(self.COLUMNS) - 1, object=datasets[-1]
            )
            self.dataChanged.emit(top_left_index, bottom_right_index)

    def _on_dataset_nested_event(self, event: Event) -> None:
        assert isinstance(event.source_event, Event)
        column = next(
            (
                column_index
                for column_index, column in enumerate(self.COLUMNS)
                if column.field == event.source_event.type
            ),
            None,
        )
        if column is not None:
            dataset = event.source_event.source
            assert isinstance(dataset, Dataset)
            index = self.create_dataset_index(dataset, column=column)
            self.dataChanged.emit(index, index)
