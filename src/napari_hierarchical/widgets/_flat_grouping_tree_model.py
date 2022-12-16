import logging
from enum import IntEnum
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence

from napari.utils.events import Event, EventedDict, EventedList
from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt

from .._controller import HierarchicalController
from ..model import Array
from ..utils.parent_aware import ParentAware

logger = logging.getLogger(__name__)


class Arrays(List[Array]):
    def __init__(self, flat_group: str, iterable: Iterable[Array]) -> None:
        super().__init__(iterable)
        self.flat_group = flat_group

    def __repr__(self) -> str:
        return self.flat_group


class QFlatGroupingTreeModel(QAbstractItemModel):
    class COLUMNS(IntEnum):
        NAME = 0
        LOADED = 1
        VISIBLE = 2

    def __init__(
        self,
        controller: HierarchicalController,
        flat_grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._flat_grouping = flat_grouping
        self._close_callback = close_callback
        self._dropping = False
        self._flat_groups: List[str] = []
        self._flat_group_arrays: Dict[str, Arrays] = {}
        for array in controller.current_arrays:
            if flat_grouping is None or flat_grouping in array.flat_grouping_groups:
                flat_group = self._get_flat_group(array)
                if flat_group not in self._flat_groups:
                    self._flat_groups.append(flat_group)
                    self._flat_group_arrays[flat_group] = Arrays(flat_group, [array])
                else:
                    self._flat_group_arrays[flat_group].append(array)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        for array in self._controller.current_arrays:
            self._connect_array_events(array)
        self._controller.current_arrays.events.connect(self._on_current_arrays_event)

    def _disconnect_events(self) -> None:
        self._controller.current_arrays.events.disconnect(self._on_current_arrays_event)
        for array in self._controller.current_arrays:
            self._disconnect_array_events(array)

    def _connect_array_events(self, array: Array) -> None:
        if self._flat_grouping is not None:
            array.flat_grouping_groups.events.connect(
                self._on_flat_grouping_groups_event
            )
        else:
            array.events.name.connect(self._on_array_name_event)
        array.events.loaded.connect(self._on_array_loaded_event)
        array.events.visible.connect(self._on_array_visible_event)

    def _disconnect_array_events(self, array: Array) -> None:
        if self._flat_grouping is not None:
            array.flat_grouping_groups.events.disconnect(
                self._on_flat_grouping_groups_event
            )
        else:
            array.events.name.disconnect(self._on_array_name_event)
        array.events.loaded.disconnect(self._on_array_loaded_event)
        array.events.visible.disconnect(self._on_array_visible_event)

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if 0 <= column < len(self.COLUMNS):
            if parent.isValid():
                if parent.column() == self.COLUMNS.NAME:
                    arrays = parent.internalPointer()
                    assert isinstance(arrays, Arrays)
                    if 0 <= row < len(arrays):
                        return self.createIndex(row, column, object=arrays[row])
            elif 0 <= row < len(self._flat_groups):
                flat_group = self._flat_groups[row]
                arrays = self._flat_group_arrays[flat_group]
                return self.createIndex(row, column, object=arrays)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if index.isValid():
            array_or_arrays = index.internalPointer()
            assert isinstance(array_or_arrays, (Array, Arrays))
            if isinstance(array_or_arrays, Array):
                array = array_or_arrays
                flat_group = self._get_flat_group(array)
                return self.create_flat_group_index(flat_group)
        return QModelIndex()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            if parent.column() == self.COLUMNS.NAME:
                array_or_arrays = parent.internalPointer()
                assert isinstance(array_or_arrays, (Array, Arrays))
                if (
                    isinstance(array_or_arrays, Arrays)
                    and self._flat_grouping is not None
                ):
                    arrays = array_or_arrays
                    return len(arrays)
            return 0
        return len(self._flat_groups)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid():
            assert 0 <= index.column() < len(self.COLUMNS)
            array_or_arrays = index.internalPointer()
            assert isinstance(array_or_arrays, (Array, Arrays))
            if isinstance(array_or_arrays, Array):
                array = array_or_arrays
                if index.column() == self.COLUMNS.NAME:
                    # if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole)
                    if role == Qt.ItemDataRole.DisplayRole:
                        return array.name
                elif index.column() == self.COLUMNS.LOADED:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        if array.loaded:
                            return Qt.CheckState.Checked
                        return Qt.CheckState.Unchecked
                elif index.column() == self.COLUMNS.VISIBLE:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        if array.visible:
                            return Qt.CheckState.Checked
                        return Qt.CheckState.Unchecked
                else:
                    raise NotImplementedError()
            else:
                arrays = array_or_arrays
                if index.column() == self.COLUMNS.NAME:
                    # if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole)
                    if role == Qt.ItemDataRole.DisplayRole:
                        return arrays.flat_group
                elif index.column() == self.COLUMNS.LOADED:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        # evaluate any before all to catch empty iterables!
                        if not any(array.loaded for array in arrays):
                            return Qt.CheckState.Unchecked
                        if all(array.loaded for array in arrays):
                            return Qt.CheckState.Checked
                        return Qt.CheckState.PartiallyChecked
                elif index.column() == self.COLUMNS.VISIBLE:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        # evaluate any before all to catch empty iterables!
                        if not any(array.visible for array in arrays if array.loaded):
                            return Qt.CheckState.Unchecked
                        if all(array.visible for array in arrays if array.loaded):
                            return Qt.CheckState.Checked
                        return Qt.CheckState.PartiallyChecked
                else:
                    raise NotImplementedError()
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if index.isValid():
            assert 0 <= index.column() < len(self.COLUMNS)
            array_or_arrays = index.internalPointer()
            assert isinstance(array_or_arrays, (Array, Arrays))
            logger.debug(f"array_or_arrays={array_or_arrays}, value={value}")
            if isinstance(array_or_arrays, Array):
                array = array_or_arrays
                # if index.column() == self.COLUMNS.NAME:
                #     if role == Qt.ItemDataRole.EditRole:
                #         assert isinstance(value, str)
                #         array.name = value
                #         return True
                if index.column() == self.COLUMNS.LOADED:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                        if value == Qt.CheckState.Checked:
                            self._controller.load_array(array)
                        else:
                            self._controller.unload_array(array)
                        return True
                elif index.column() == self.COLUMNS.VISIBLE:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                        if value == Qt.CheckState.Checked:
                            array.show()
                        else:
                            array.hide()
                        return True
                else:
                    raise NotImplementedError()
            else:
                arrays = array_or_arrays
                # if index.column() == self.COLUMNS.NAME:
                #     if role == Qt.ItemDataRole.EditRole:
                #         assert isinstance(value, str)
                #         if value not in self._flat_groups:
                #             for array in arrays:
                #                 self._set_flat_group(array, value)
                #             return True
                if index.column() == self.COLUMNS.LOADED:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                        if value == Qt.CheckState.Checked:
                            for array in arrays:
                                if not array.loaded:
                                    self._controller.load_array(array)
                        else:
                            for array in arrays:
                                if array.loaded:
                                    self._controller.unload_array(array)
                        return True
                elif index.column() == self.COLUMNS.VISIBLE:
                    if role == Qt.ItemDataRole.CheckStateRole:
                        assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                        if value == Qt.CheckState.Checked:
                            for array in arrays:
                                if array.loaded and not array.visible:
                                    array.show()
                        else:
                            for array in arrays:
                                if array.loaded and array.visible:
                                    array.hide()
                        return True
                else:
                    raise NotImplementedError()
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.isValid():
            array_or_arrays = index.internalPointer()
            assert isinstance(array_or_arrays, (Array, Arrays))
            if isinstance(array_or_arrays, Array):
                array = array_or_arrays
                if index.column() == self.COLUMNS.NAME:
                    flags = (
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        # | Qt.ItemFlag.ItemIsEditable
                        | Qt.ItemFlag.ItemNeverHasChildren
                    )
                    # if array.loaded:
                    #     flags |= Qt.ItemFlag.ItemIsDragEnabled
                    return flags
                if index.column() == self.COLUMNS.LOADED:
                    flags = (
                        Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                        | Qt.ItemFlag.ItemNeverHasChildren
                    )
                    if self._controller.can_load_array(array):
                        flags |= Qt.ItemFlag.ItemIsEnabled
                    # if array.loaded:
                    #     flags |= Qt.ItemFlag.ItemIsDragEnabled
                    return flags
                if index.column() == self.COLUMNS.VISIBLE:
                    flags = (
                        Qt.ItemFlag.ItemIsSelectable
                        | Qt.ItemFlag.ItemIsUserCheckable
                        | Qt.ItemFlag.ItemNeverHasChildren
                    )
                    if array.loaded:
                        flags |= Qt.ItemFlag.ItemIsEnabled
                    # if array.loaded:
                    #     flags |= Qt.ItemFlag.ItemIsDragEnabled
                    return flags
            else:
                arrays = array_or_arrays
                if index.column() == self.COLUMNS.NAME:
                    flags = (
                        Qt.ItemFlag.ItemIsEnabled
                        | Qt.ItemFlag.ItemIsSelectable
                        # | Qt.ItemFlag.ItemIsEditable
                    )
                    # if self._flat_grouping is not None:
                    #     flags |= Qt.ItemFlag.ItemIsDropEnabled
                    if self._flat_grouping is None:
                        flags |= Qt.ItemFlag.ItemNeverHasChildren
                    return flags
                if index.column() == self.COLUMNS.LOADED:
                    flags = (
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    if not any(array.loaded for array in arrays) or all(
                        array.loaded for array in arrays
                    ):  # load/unload all
                        if all(
                            self._controller.can_load_array(array) for array in arrays
                        ):
                            flags |= Qt.ItemFlag.ItemIsEnabled
                    else:  # only load remaining
                        if all(
                            self._controller.can_load_array(array)
                            for array in arrays
                            if not array.loaded
                        ):
                            flags |= Qt.ItemFlag.ItemIsEnabled
                    # if self._flat_grouping is not None:
                    #     flags |= Qt.ItemFlag.ItemIsDropEnabled
                    if self._flat_grouping is None:
                        flags |= Qt.ItemFlag.ItemNeverHasChildren
                    return flags
                if index.column() == self.COLUMNS.VISIBLE:
                    flags = (
                        Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
                    )
                    if any(array.loaded for array in arrays):
                        flags |= Qt.ItemFlag.ItemIsEnabled
                    # if self._flat_grouping is not None:
                    #     flags |= Qt.ItemFlag.ItemIsDropEnabled
                    if self._flat_grouping is None:
                        flags |= Qt.ItemFlag.ItemNeverHasChildren
                    return flags
        return super().flags(index)

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
                if self._flat_grouping is not None:
                    return "Array grouping"
                return "Array"
            if section == self.COLUMNS.LOADED:
                return "L"
            if section == self.COLUMNS.VISIBLE:
                return "V"
        return None

    # def supportedDropActions(self) -> Qt.DropActions:
    #     return Qt.DropAction.MoveAction

    # def mimeTypes(self) -> List[str]:
    #     mime_types = super().mimeTypes()
    #     mime_types.append("x-napari-hierarchical-array")
    #     return mime_types

    # def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
    #     data = super().mimeData(indexes)
    #     indices_stacks = []
    #     for index in indexes:
    #         if index.column() == 0:
    #             array = index.internalPointer()
    #             assert isinstance(array, Array)
    #             group = array.parent
    #             assert isinstance(group, Group)
    #             indices_stack = [group.arrays.index(array)]
    #             while group.parent is not None:
    #                 indices_stack.append(group.parent.children.index(group))
    #                 group = group.parent
    #             indices_stack.append(self._controller.groups.index(group))
    #             indices_stacks.append(indices_stack)
    #     data.setData("x-napari-hierarchical-array", pickle.dumps(indices_stacks))
    #     return data

    # def dropMimeData(
    #     self,
    #     data: QMimeData,
    #     action: Qt.DropAction,
    #     row: int,
    #     column: int,
    #     parent: QModelIndex,
    # ) -> bool:
    #     if (
    #         data.hasFormat("x-napari-hierarchical-array")
    #         and action == Qt.DropAction.MoveAction
    #     ):
    #         assert row == -1
    #         assert column == -1
    #         assert parent.isValid()
    #         target_arrays = parent.internalPointer()
    #         assert isinstance(target_arrays, Arrays)
    #         indices_stacks = pickle.loads(
    #             data.data("x-napari-hierarchical-array").data()
    #         )
    #         assert isinstance(indices_stacks, List) and len(indices_stacks) > 0
    #         while len(indices_stacks) > 0:
    #             indices_stack = indices_stacks.pop(0)
    #             assert isinstance(indices_stack, List) and len(indices_stack) > 1
    #             source_groups = self._controller.groups
    #             source_row = indices_stack.pop()
    #             assert isinstance(source_row, int)
    #             while len(indices_stack) > 1:
    #                 source_groups = source_groups[source_row].children
    #                 source_row = indices_stack.pop()
    #                 assert isinstance(source_row, int)
    #             group = source_groups[source_row]
    #             array = group.arrays[indices_stack.pop()]
    #             logger.debug(f"target_arrays={target_arrays}, array={array}")
    #             self._dropping = True
    #             try:
    #                 new_array = Array.from_array(array)
    #                 self._set_flat_group(new_array, target_arrays.flat_group)
    #                 group.arrays.append(new_array)
    #             finally:
    #                 self._dropping = False
    #         return True
    #     return False

    # def removeRows(
    #     self, row: int, count: int, parent: QModelIndex = QModelIndex()
    # ) -> bool:
    #     if parent.isValid():
    #         arrays = parent.internalPointer()
    #         assert isinstance(arrays, Arrays)
    #         if 0 <= row < row + count <= len(arrays):
    #             arrays_copy = [arrays[i] for i in range(row, row + count)]
    #             for array in arrays_copy:
    #                 group = array.parent
    #                 assert group is not None
    #                 logger.debug(f"arrays={group.arrays}, array={array}")
    #                 group.arrays.remove(array)
    #             return True
    #     return False

    def create_array_index(self, array: Array, column: int = 0) -> QModelIndex:
        flat_group = self._get_flat_group(array)
        row = self._flat_group_arrays[flat_group].index(array)
        return self.createIndex(row, column, object=array)

    def create_flat_group_index(self, flat_group: str, column: int = 0) -> QModelIndex:
        row = self._flat_groups.index(flat_group)
        arrays = self._flat_group_arrays[flat_group]
        return self.createIndex(row, column, object=arrays)

    def _on_current_arrays_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type == "inserted":
            logger.debug(f"event={event.type}")
            array = event.value
            assert isinstance(array, Array)
            if (
                self._flat_grouping is None
                or self._flat_grouping in array.flat_grouping_groups
            ):
                flat_group = self._get_flat_group(array)
                self._add_array_to_flat_group(array, flat_group)
            self._connect_array_events(array)
        elif event.type == "removed":
            logger.debug(f"event={event.type}")
            array = event.value
            assert isinstance(array, Array)
            self._disconnect_array_events(array)
            if (
                self._flat_grouping is None
                or self._flat_grouping in array.flat_grouping_groups
            ):
                flat_group = self._get_flat_group(array)
                self._remove_array_from_flat_group(array, flat_group)
                self._close_if_empty()
        elif event.type == "changed" and isinstance(event.index, int):
            logger.debug(f"event={event.type}")
            old_array = event.old_value
            assert isinstance(old_array, Array)
            self._disconnect_array_events(old_array)
            if (
                self._flat_grouping is None
                or self._flat_grouping in old_array.flat_grouping_groups
            ):
                old_flat_group = self._get_flat_group(old_array)
                self._remove_array_from_flat_group(old_array, old_flat_group)
            array = event.value
            assert isinstance(array, Array)
            if (
                self._flat_grouping is None
                or self._flat_grouping in array.flat_grouping_groups
            ):
                flat_group = self._get_flat_group(array)
                self._add_array_to_flat_group(array, flat_group)
            self._connect_array_events(array)
            self._close_if_empty()
        elif event.type == "changed":
            logger.debug(f"event={event.type}")
            old_arrays = event.old_value
            assert isinstance(old_arrays, List)
            for old_array in old_arrays:
                assert isinstance(old_array, Array)
                self._disconnect_array_events(old_array)
                if (
                    self._flat_grouping is None
                    or self._flat_grouping in old_array.flat_grouping_groups
                ):
                    old_flat_group = self._get_flat_group(old_array)
                    self._remove_array_from_flat_group(old_array, old_flat_group)
            arrays = event.value
            assert isinstance(arrays, List)
            for array in arrays:
                assert isinstance(array, Array)
                if (
                    self._flat_grouping is None
                    or self._flat_grouping in array.flat_grouping_groups
                ):
                    flat_group = self._get_flat_group(array)
                    self._add_array_to_flat_group(array, flat_group)
                self._connect_array_events(array)
            self._close_if_empty()

    def _on_flat_grouping_groups_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedDict):
            return
        assert self._flat_grouping is not None
        flat_grouping_groups = event.source
        assert isinstance(flat_grouping_groups, ParentAware)
        array = flat_grouping_groups.parent
        assert isinstance(array, Array)
        if event.type == "added" and event.key == self._flat_grouping:
            logger.debug(f"event={event.type}")
            flat_group = event.value
            assert isinstance(flat_group, str)
            self._add_array_to_flat_group(array, flat_group)
        elif event.type == "removed" and event.key == self._flat_grouping:
            logger.debug(f"event={event.type}")
            flat_group = event.value
            assert isinstance(flat_group, str)
            self._remove_array_from_flat_group(array, flat_group)
            self._close_if_empty()
        elif event.type == "changed" and event.key == self._flat_grouping:
            logger.debug(f"event={event.type}")
            old_flat_group = event.old_value
            assert isinstance(old_flat_group, str)
            self._remove_array_from_flat_group(array, old_flat_group)
            flat_group = event.value
            assert isinstance(flat_group, str)
            self._add_array_to_flat_group(array, flat_group)

    def _on_array_name_event(self, event: Event) -> None:
        logger.debug(f"event={event.type}")
        assert self._flat_grouping is None
        array = event.source
        assert isinstance(array, Array)
        old_flat_group = next(
            flat_group
            for flat_group, arrays in self._flat_group_arrays.items()
            if array in arrays
        )
        self._remove_array_from_flat_group(array, old_flat_group)
        flat_group = self._get_flat_group(array)
        self._add_array_to_flat_group(array, flat_group)

    def _on_array_loaded_event(self, event: Event) -> None:
        array = event.source
        assert isinstance(array, Array)
        if (
            self._flat_grouping is None
            or self._flat_grouping in array.flat_grouping_groups
        ):
            logger.debug(f"event={event.type}")
            if self._flat_grouping is not None:
                array_index = self.create_array_index(array, column=self.COLUMNS.LOADED)
                self.dataChanged.emit(array_index, array_index)
            flat_group = self._get_flat_group(array)
            flat_group_index = self.create_flat_group_index(
                flat_group, column=self.COLUMNS.LOADED
            )
            self.dataChanged.emit(flat_group_index, flat_group_index)

    def _on_array_visible_event(self, event: Event) -> None:
        array = event.source
        assert isinstance(array, Array)
        if (
            self._flat_grouping is None
            or self._flat_grouping in array.flat_grouping_groups
        ):
            logger.debug(f"event={event.type}")
            if self._flat_grouping is not None:
                array_index = self.create_array_index(
                    array, column=self.COLUMNS.VISIBLE
                )
                self.dataChanged.emit(array_index, array_index)
            flat_group = self._get_flat_group(array)
            flat_group_index = self.create_flat_group_index(
                flat_group, column=self.COLUMNS.VISIBLE
            )
            self.dataChanged.emit(flat_group_index, flat_group_index)

    def _add_array_to_flat_group(self, array: Array, flat_group: str) -> None:
        if flat_group not in self._flat_groups:
            logger.debug(f"array={array}, flat_group={flat_group} [add group]")
            flat_group_row = len(self._flat_groups)
            self.beginInsertRows(QModelIndex(), flat_group_row, flat_group_row)
            self._flat_groups.insert(flat_group_row, flat_group)
            self._flat_group_arrays[flat_group] = Arrays(flat_group, [array])
            self.endInsertRows()
        else:
            logger.debug(f"array={array}, flat_group={flat_group}")
            array_row = len(self._flat_group_arrays[flat_group])
            if self._flat_grouping is not None:
                flat_group_index = self.create_flat_group_index(flat_group)
                self.beginInsertRows(flat_group_index, array_row, array_row)
            self._flat_group_arrays[flat_group].insert(array_row, array)
            if self._flat_grouping is not None:
                self.endInsertRows()
            first_flat_group_index = self.create_flat_group_index(
                flat_group, column=self.COLUMNS.LOADED
            )
            last_flat_group_index = self.create_flat_group_index(
                flat_group, column=self.COLUMNS.VISIBLE
            )
            self.dataChanged.emit(first_flat_group_index, last_flat_group_index)

    def _remove_array_from_flat_group(self, array: Array, flat_group: str) -> None:
        if any(a != array for a in self._flat_group_arrays[flat_group]):
            logger.debug(f"array={array}, flat_group={flat_group}")
            array_row = self._flat_group_arrays[flat_group].index(array)
            if self._flat_grouping is not None:
                flat_group_index = self.create_flat_group_index(flat_group)
                self.beginRemoveRows(flat_group_index, array_row, array_row)
            del self._flat_group_arrays[flat_group][array_row]
            if self._flat_grouping is not None:
                self.endRemoveRows()
            first_flat_group_index = self.create_flat_group_index(
                flat_group, column=self.COLUMNS.LOADED
            )
            last_flat_group_index = self.create_flat_group_index(
                flat_group, column=self.COLUMNS.VISIBLE
            )
            self.dataChanged.emit(first_flat_group_index, last_flat_group_index)
        else:
            logger.debug(f"array={array}, flat_group={flat_group} [remove group]")
            flat_group_row = self._flat_groups.index(flat_group)
            self.beginRemoveRows(QModelIndex(), flat_group_row, flat_group_row)
            del self._flat_groups[flat_group_row]
            del self._flat_group_arrays[flat_group]
            self.endRemoveRows()

    def _get_flat_group(self, array: Array) -> str:
        if self._flat_grouping is not None:
            return array.flat_grouping_groups[self._flat_grouping]
        return array.name

    # def _set_flat_group(self, array: Array, value: str) -> None:
    #     logger.debug(f"array={array}, value={value}")
    #     if self._flat_grouping is not None:
    #         array.flat_grouping_groups[self._flat_grouping] = value
    #     else:
    #         array.name = value

    def _close_if_empty(self) -> None:
        if len(self._flat_groups) == 0 and self._close_callback is not None:
            logger.debug("")
            self._disconnect_events()
            self._close_callback()

    @property
    def flat_grouping(self) -> Optional[str]:
        return self._flat_grouping

    @property
    def flat_groups(self) -> Sequence[str]:
        return self._flat_groups

    @property
    def flat_group_arrays(self) -> Mapping[str, Arrays]:
        return self._flat_group_arrays

    @property
    def dropping(self) -> bool:
        return self._dropping
