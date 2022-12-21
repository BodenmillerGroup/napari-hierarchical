import logging
import pickle
from enum import IntEnum
from typing import Any, Iterable, List, Optional

from napari.utils.events import Event, EventedList
from qtpy.QtCore import QAbstractItemModel, QMimeData, QModelIndex, QObject, Qt

from .._controller import HierarchicalController
from ..model import Group
from ..utils.parent_aware import ParentAware

logger = logging.getLogger(__name__)


class QGroupTreeModel(QAbstractItemModel):
    class COLUMNS(IntEnum):
        NAME = 0
        LOADED = 1
        VISIBLE = 2

    def __init__(
        self, controller: HierarchicalController, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._dropping = False
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        for group in self._controller.groups:
            self._connect_group_events(group)
        self._controller.groups.events.connect(self._on_groups_event)

    def _disconnect_events(self) -> None:
        self._controller.groups.events.disconnect(self._on_groups_event)
        for group in self._controller.groups:
            self._disconnect_group_events(group)

    def _connect_group_events(self, group: Group) -> None:
        group.nested_event.connect(self._on_group_nested_event)
        group.nested_list_event.connect(self._on_group_nested_list_event)

    def _disconnect_group_events(self, group: Group) -> None:
        group.nested_event.disconnect(self._on_group_nested_event)
        group.nested_list_event.disconnect(self._on_group_nested_list_event)

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if 0 <= column < len(self.COLUMNS):
            if parent.isValid():
                if parent.column() == self.COLUMNS.NAME:
                    parent_group = parent.internalPointer()
                    assert isinstance(parent_group, Group)
                    if 0 <= row < len(parent_group.children):
                        group = parent_group.children[row]
                        return self.createIndex(row, column, object=group)
            elif 0 <= row < len(self._controller.groups):
                group = self._controller.groups[row]
                return self.createIndex(row, column, object=group)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if index.isValid():
            group = index.internalPointer()
            assert isinstance(group, Group)
            if group.parent is not None:
                return self.create_group_index(group.parent)
        return QModelIndex()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            if parent.column() == self.COLUMNS.NAME:
                group = parent.internalPointer()
                assert isinstance(group, Group)
                return len(group.children)
            return 0
        return len(self._controller.groups)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid():
            group = index.internalPointer()
            assert isinstance(group, Group)
            assert 0 <= index.column() < len(self.COLUMNS)
            if index.column() == self.COLUMNS.NAME:
                if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
                    return group.name
            elif index.column() == self.COLUMNS.LOADED:
                if role == Qt.ItemDataRole.CheckStateRole:
                    if group.loaded is None:
                        return Qt.CheckState.PartiallyChecked
                    if group.loaded:
                        return Qt.CheckState.Checked
                    return Qt.CheckState.Unchecked
            elif index.column() == self.COLUMNS.VISIBLE:
                if role == Qt.ItemDataRole.CheckStateRole:
                    if group.visible is None:
                        return Qt.CheckState.PartiallyChecked
                    if group.visible:
                        return Qt.CheckState.Checked
                    return Qt.CheckState.Unchecked
            else:
                raise NotImplementedError()
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if index.isValid():
            group = index.internalPointer()
            assert isinstance(group, Group)
            assert 0 <= index.column() < len(self.COLUMNS)
            if index.column() == self.COLUMNS.NAME:
                if role == Qt.ItemDataRole.EditRole:
                    logger.debug(f"group={group}, value={value}")
                    assert isinstance(value, str)
                    group.name = value
                    return True
            elif index.column() == self.COLUMNS.LOADED:
                if role == Qt.ItemDataRole.CheckStateRole:
                    logger.debug(f"group={group}, value={value}")
                    assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                    if value == Qt.CheckState.Checked:
                        self._controller.load_group(group)
                    else:
                        self._controller.unload_group(group)
                    return True
            elif index.column() == self.COLUMNS.VISIBLE:
                if role == Qt.ItemDataRole.CheckStateRole:
                    logger.debug(f"group={group}, value={value}")
                    assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                    if value == Qt.CheckState.Checked:
                        group.show()
                    else:
                        group.hide()
                    return True
            else:
                raise NotImplementedError()
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.isValid():
            group = index.internalPointer()
            assert isinstance(group, Group)
            assert 0 <= index.column() < len(self.COLUMNS)
            if index.column() == self.COLUMNS.NAME:
                flags = (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsEditable
                    | Qt.ItemFlag.ItemIsDropEnabled
                )
                if group.loaded:
                    flags |= Qt.ItemFlag.ItemIsDragEnabled
                return flags
            if index.column() == self.COLUMNS.LOADED:
                flags = (
                    Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsDropEnabled
                )
                if (
                    group.loaded is not None  # load/unload all
                    and self._controller.can_load_group(group)
                ) or (
                    group.loaded is None  # only load remaining
                    and self._controller.can_load_group(group, unloaded_only=True)
                ):
                    flags |= Qt.ItemFlag.ItemIsEnabled
                if group.loaded:
                    flags |= Qt.ItemFlag.ItemIsDragEnabled
                return flags
            if index.column() == self.COLUMNS.VISIBLE:
                flags = (
                    Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsDropEnabled
                )
                if group.loaded or group.loaded is None:
                    flags |= Qt.ItemFlag.ItemIsEnabled
                if group.loaded:
                    flags |= Qt.ItemFlag.ItemIsDragEnabled
                return flags
        return super().flags(index) | Qt.ItemFlag.ItemIsDropEnabled

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            if section == self.COLUMNS.NAME:
                return "Group"
            if section == self.COLUMNS.LOADED:
                return "L"
            if section == self.COLUMNS.VISIBLE:
                return "V"
        return None

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.DropAction.MoveAction

    def mimeTypes(self) -> List[str]:
        mime_types = super().mimeTypes()
        mime_types.append("x-napari-hierarchical-group")
        mime_types.append("x-napari-hierarchical-array")
        return mime_types

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        data = super().mimeData(indexes)
        indices_stacks = []
        for index in indexes:
            if index.column() == 0:
                group = index.internalPointer()
                assert isinstance(group, Group)
                indices_stack = []
                while group.parent is not None:
                    indices_stack.append(group.parent.children.index(group))
                    group = group.parent
                indices_stack.append(self._controller.groups.index(group))
                indices_stacks.append(indices_stack)
        data.setData("x-napari-hierarchical-group", pickle.dumps(indices_stacks))
        return data

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if (
            data.hasFormat("x-napari-hierarchical-group")
            and action == Qt.DropAction.MoveAction
        ):
            if parent.isValid():
                parent_group = parent.internalPointer()
                assert isinstance(parent_group, Group)
                target_groups = parent_group.children
            else:
                target_groups = self._controller.groups
            if row == -1 and column == -1:
                row = len(target_groups)
            assert 0 <= row <= len(target_groups)
            indices_stacks = pickle.loads(
                data.data("x-napari-hierarchical-group").data()
            )
            assert isinstance(indices_stacks, List) and len(indices_stacks) > 0
            row_offset = 0
            while len(indices_stacks) > 0:
                indices_stack = indices_stacks.pop(0)
                assert isinstance(indices_stack, List) and len(indices_stack) > 0
                source_groups = self._controller.groups
                source_row = indices_stack.pop()
                assert isinstance(source_row, int)
                while len(indices_stack) > 0:
                    source_groups = source_groups[source_row].children
                    source_row = indices_stack.pop()
                    assert isinstance(source_row, int)
                group = source_groups[source_row]
                logger.debug(f"target_groups={target_groups}, group={group}")
                self._dropping = True
                try:
                    new_group = Group.from_group(group)
                    target_groups.insert(row + row_offset, new_group)
                finally:
                    self._dropping = False
                row_offset += 1
            return True
        # if (
        #     data.hasFormat("x-napari-hierarchical-array")
        #     and action == Qt.DropAction.MoveAction
        #     and row == -1
        #     and column == -1
        #     and parent.isValid()
        # ):
        #     pass
        return False

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if parent.isValid():
            parent_group = parent.internalPointer()
            assert isinstance(parent_group, Group)
            groups = parent_group.children
        else:
            groups = self._controller.groups
        if 0 <= row < row + count <= len(groups):
            groups_copy = [groups[i] for i in range(row, row + count)]
            for group in groups_copy:
                logger.debug(f"groups={groups}, group={group}")
                for array in group.iter_arrays(recursive=True):
                    array.layer = None
                groups.remove(group)
            return True
        return False

    def create_group_index(self, group: Group, column: int = 0) -> QModelIndex:
        if group.parent is not None:
            parent_groups = group.parent.children
        else:
            parent_groups = self._controller.groups
        row = parent_groups.index(group)
        return self.createIndex(row, column, object=group)

    def _on_groups_event(self, event: Event) -> None:
        self._process_groups_event(event, connect=True)

    def _on_group_nested_list_event(self, event: Event) -> None:
        source_list_event = event.source_list_event
        assert isinstance(source_list_event, Event)
        group_children = source_list_event.source
        assert isinstance(group_children, ParentAware)
        group = group_children.parent
        assert isinstance(group, Group)
        if group_children == group.children:
            self._process_groups_event(source_list_event)

    def _process_groups_event(self, event: Event, connect: bool = False) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        groups = event.source
        assert isinstance(groups, EventedList)

        def get_parent_index() -> QModelIndex:
            if isinstance(groups, ParentAware):
                assert isinstance(groups.parent, Group)
                return self.create_group_index(groups.parent)
            return QModelIndex()

        if event.type == "inserting":
            logger.debug(f"event={event.type}")
            assert isinstance(event.index, int) and 0 <= event.index <= len(groups)
            self.beginInsertRows(get_parent_index(), event.index, event.index)
        elif event.type == "inserted":
            logger.debug(f"event={event.type}")
            self.endInsertRows()
            if connect:
                group = event.value
                assert isinstance(group, Group)
                self._connect_group_events(group)
        elif event.type == "removing":
            logger.debug(f"event={event.type}")
            assert isinstance(event.index, int) and 0 <= event.index < len(groups)
            if connect:
                group = groups[event.index]
                assert isinstance(group, Group)
                self._disconnect_group_events(group)
            self.beginRemoveRows(get_parent_index(), event.index, event.index)
        elif event.type == "removed":
            logger.debug(f"event={event.type}")
            self.endRemoveRows()
        elif event.type == "moving":
            logger.debug(f"event={event.type}")
            assert isinstance(event.index, int) and 0 <= event.index < len(groups)
            assert (
                isinstance(event.new_index, int)
                and 0 <= event.new_index <= len(groups)
                and event.new_index != event.index
            )
            parent_index = get_parent_index()
            self.beginMoveRows(
                parent_index, event.index, event.index, parent_index, event.new_index
            )
        elif event.type == "moved":
            logger.debug(f"event={event.type}")
            self.endMoveRows()
        elif event.type == "changed" and isinstance(event.index, int):
            logger.debug(f"event={event.type}")
            assert 0 <= event.index < len(groups)
            if connect:
                old_group = event.old_value
                assert isinstance(old_group, Group)
                self._disconnect_group_events(old_group)
                group = event.value
                assert isinstance(group, Group)
                self._connect_group_events(group)
            left_index = self.createIndex(event.index, 0, object=groups[event.index])
            right_index = self.createIndex(
                event.index, len(self.COLUMNS) - 1, object=groups[event.index]
            )
            self.dataChanged.emit(left_index, right_index)
        elif event.type == "changed":
            logger.debug(f"event={event.type}")
            if connect:
                old_groups = event.old_value
                assert isinstance(old_groups, List)
                for old_group in old_groups:
                    assert isinstance(old_group, Group)
                    self._disconnect_group_events(old_group)
                groups = event.value
                assert isinstance(groups, List)
                for group in groups:
                    assert isinstance(group, Group)
                    self._connect_group_events(group)
            top_left_index = self.createIndex(0, 0, object=groups[0])
            bottom_right_index = self.createIndex(
                len(groups) - 1, len(self.COLUMNS) - 1, object=groups[-1]
            )
            self.dataChanged.emit(top_left_index, bottom_right_index)
        elif event.type == "reordered":
            logger.debug(f"event={event.type}")
            top_left_index = self.createIndex(0, 0, object=groups[0])
            bottom_right_index = self.createIndex(
                len(groups) - 1, len(self.COLUMNS) - 1, object=groups[-1]
            )
            self.dataChanged.emit(top_left_index, bottom_right_index)

    def _on_group_nested_event(self, event: Event) -> None:
        source_event = event.source_event
        assert isinstance(source_event, Event)
        column = None
        if source_event.type == "name":
            column = self.COLUMNS.NAME
        elif source_event.type == "loaded":
            column = self.COLUMNS.LOADED
        elif source_event.type == "visible":
            column = self.COLUMNS.VISIBLE
        if column is not None:
            logger.debug(f"source_event={source_event.type}")
            group = source_event.source
            assert isinstance(group, Group)
            index = self.create_group_index(group, column=column)
            self.dataChanged.emit(index, index)

    @property
    def dropping(self) -> bool:
        return self._dropping
