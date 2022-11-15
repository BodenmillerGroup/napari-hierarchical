from enum import IntEnum
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from napari.utils.events import Event, EventedDict, EventedList
from qtpy.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

from .._controller import HierarchicalController
from ..model import Array
from ..utils.parent_aware import ParentAware


# TODO make array groupings user-editable --> QTreeModel
# TODO drag arrays onto group
class QArrayGroupTableModel(QAbstractTableModel):
    class COLUMNS(IntEnum):
        NAME = 0
        LOADED = 1
        VISIBLE = 2

    def __init__(
        self,
        controller: HierarchicalController,
        array_grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._array_grouping = array_grouping
        self._close_callback = close_callback
        self._array_groups: List[str] = []
        self._array_group_arrays: Dict[str, List[Array]] = {}
        for array in controller.current_arrays:
            if array_grouping is None or array_grouping in array.array_grouping_groups:
                array_group = self._get_array_group(array)
                self._add_array_to_array_group(array, array_group, initializing=True)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._array_groups)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid():
            assert 0 <= index.row() < len(self._array_groups)
            assert 0 <= index.column() < len(self.COLUMNS)
            array_group = self._array_groups[index.row()]
            if index.column() == self.COLUMNS.NAME:
                if role == Qt.ItemDataRole.DisplayRole:
                    return array_group
            elif index.column() == self.COLUMNS.LOADED:
                if role == Qt.ItemDataRole.CheckStateRole:
                    arrays = self._array_group_arrays[array_group]
                    loaded_arrays = [array for array in arrays if array.loaded]
                    if len(loaded_arrays) == 0:
                        return Qt.CheckState.Unchecked
                    if len(loaded_arrays) == len(arrays):
                        return Qt.CheckState.Checked
                    return Qt.CheckState.PartiallyChecked
            elif index.column() == self.COLUMNS.VISIBLE:
                if role == Qt.ItemDataRole.CheckStateRole:
                    arrays = self._array_group_arrays[array_group]
                    visible_arrays = [array for array in arrays if array.visible]
                    if len(visible_arrays) == 0:
                        return Qt.CheckState.Unchecked
                    if len(visible_arrays) == len(arrays):
                        return Qt.CheckState.Checked
                    return Qt.CheckState.PartiallyChecked
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if index.isValid():
            assert 0 <= index.row() < len(self._array_groups)
            assert 0 <= index.column() < len(self.COLUMNS)
            array_group = self._array_groups[index.row()]
            if index.column() == self.COLUMNS.LOADED:
                if role == Qt.ItemDataRole.CheckStateRole:
                    assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                    if value == Qt.CheckState.Checked:
                        for array in self._array_group_arrays[array_group]:
                            self._controller.load_array(array)
                    else:
                        for array in self._array_group_arrays[array_group]:
                            self._controller.unload_array(array)
                    return True
            elif index.column() == self.COLUMNS.VISIBLE:
                if role == Qt.ItemDataRole.CheckStateRole:
                    assert value in (Qt.CheckState.Checked, Qt.CheckState.Unchecked)
                    if value == Qt.CheckState.Checked:
                        for array in self._array_group_arrays[array_group]:
                            array.show()
                    else:
                        for array in self._array_group_arrays[array_group]:
                            array.hide()
                    return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if index.isValid():
            assert 0 <= index.row() < len(self._array_groups)
            assert 0 <= index.column() < len(self.COLUMNS)
            array_group = self._array_groups[index.row()]
            if index.column() == self.COLUMNS.NAME:
                flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                return flags
            if index.column() == self.COLUMNS.LOADED:
                flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
                if all(
                    array.loaded or self._controller.can_load_array(array)
                    for array in self._array_group_arrays[array_group]
                ):
                    flags |= Qt.ItemFlag.ItemIsEnabled
                return flags
            if index.column() == self.COLUMNS.VISIBLE:
                flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable
                if all(array.loaded for array in self._array_group_arrays[array_group]):
                    flags |= Qt.ItemFlag.ItemIsEnabled
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
                return "Array group"
            if section == self.COLUMNS.LOADED:
                return "L"
            if section == self.COLUMNS.VISIBLE:
                return "V"
        return None

    def _connect_events(self) -> None:
        self._controller.current_arrays.events.connect(self._on_current_arrays_event)
        for array in self._controller.current_arrays:
            self._connect_array_events(array)

    def _disconnect_events(self) -> None:
        for array in self._controller.current_arrays:
            self._disconnect_array_events(array)
        self._controller.current_arrays.events.disconnect(self._on_current_arrays_event)

    def _connect_array_events(self, array: Array) -> None:
        if self._array_grouping is not None:
            array.array_grouping_groups.events.connect(self._on_array_groups_event)
        else:
            array.events.name.connect(self._on_array_name_event)
        array.events.loaded.connect(self._on_array_loaded_event)
        array.events.visible.connect(self._on_array_visible_event)

    def _disconnect_array_events(self, array: Array) -> None:
        if self._array_grouping is not None:
            array.array_grouping_groups.events.disconnect(self._on_array_groups_event)
        else:
            array.events.name.disconnect(self._on_array_name_event)
        array.events.loaded.disconnect(self._on_array_loaded_event)
        array.events.visible.disconnect(self._on_array_visible_event)

    def _on_current_arrays_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type == "inserted":
            assert isinstance(event.value, Array)
            if (
                self._array_grouping is None
                or self._array_grouping in event.value.array_grouping_groups
            ):
                array_group = self._get_array_group(event.value)
                self._add_array_to_array_group(event.value, array_group)
            self._connect_array_events(event.value)
        elif event.type == "removed":
            assert isinstance(event.value, Array)
            self._disconnect_array_events(event.value)
            if (
                self._array_grouping is None
                or self._array_grouping in event.value.array_grouping_groups
            ):
                array_group = self._get_array_group(event.value)
                self._remove_array_from_array_group(event.value, array_group)
                self._close_if_empty()
        elif event.type == "changed" and isinstance(event.index, int):
            close_if_empty = False
            assert isinstance(event.old_value, Array)
            self._disconnect_array_events(event.old_value)
            if (
                self._array_grouping is None
                or self._array_grouping in event.old_value.array_grouping_groups
            ):
                old_array_group = self._get_array_group(event.old_value)
                self._remove_array_from_array_group(event.old_value, old_array_group)
                close_if_empty = True
            assert isinstance(event.value, Array)
            if (
                self._array_grouping is None
                or self._array_grouping in event.value.array_grouping_groups
            ):
                array_group = self._get_array_group(event.value)
                self._add_array_to_array_group(event.value, array_group)
                close_if_empty = False
            self._connect_array_events(event.value)
            if close_if_empty:
                self._close_if_empty()
        elif event.type == "changed":
            close_if_empty = False
            assert isinstance(event.old_value, List)
            for old_array in event.old_value:
                assert isinstance(old_array, Array)
                self._disconnect_array_events(old_array)
                if (
                    self._array_grouping is None
                    or self._array_grouping in old_array.array_grouping_groups
                ):
                    old_array_group = self._get_array_group(old_array)
                    self._remove_array_from_array_group(old_array, old_array_group)
                    close_if_empty = True
            assert isinstance(event.value, List)
            for array in event.value:
                assert isinstance(array, Array)
                if (
                    self._array_grouping is None
                    or self._array_grouping in array.array_grouping_groups
                ):
                    array_group = self._get_array_group(array)
                    self._add_array_to_array_group(array, array_group)
                    close_if_empty = False
                self._connect_array_events(array)
            if close_if_empty:
                self._close_if_empty()

    def _on_array_name_event(self, event: Event) -> None:
        assert self._array_grouping is None
        array = event.source
        assert isinstance(array, Array)
        old_array_group = next(
            array_group
            for array_group, arrays in self._array_group_arrays.items()
            if array in arrays
        )
        array_group = self._get_array_group(array)
        self._remove_array_from_array_group(array, old_array_group)
        self._add_array_to_array_group(array, array_group)

    def _on_array_loaded_event(self, event: Event) -> None:
        array = event.source
        assert isinstance(array, Array)
        if (
            self._array_grouping is None
            or self._array_grouping in array.array_grouping_groups
        ):
            array_group = self._get_array_group(array)
            row = self._array_groups.index(array_group)
            index = self.createIndex(row, self.COLUMNS.LOADED)
            self.dataChanged.emit(index, index)

    def _on_array_visible_event(self, event: Event) -> None:
        array = event.source
        assert isinstance(array, Array)
        if (
            self._array_grouping is None
            or self._array_grouping in array.array_grouping_groups
        ):
            array_group = self._get_array_group(array)
            row = self._array_groups.index(array_group)
            index = self.createIndex(row, self.COLUMNS.VISIBLE)
            self.dataChanged.emit(index, index)

    def _on_array_groups_event(self, event: Event) -> None:
        assert self._array_grouping is not None
        if not isinstance(event.sources[0], EventedDict):
            return
        array_groups = event.source
        assert isinstance(array_groups, ParentAware)
        array = array_groups.parent
        assert isinstance(array, Array)
        if event.type == "changed" and event.key == self._array_grouping:
            assert isinstance(event.old_value, str)
            self._remove_array_from_array_group(array, event.old_value)
            assert isinstance(event.value, str)
            self._add_array_to_array_group(array, event.value)
        elif event.type == "added" and event.key == self._array_grouping:
            assert isinstance(event.value, str)
            self._add_array_to_array_group(array, event.value)
        elif event.type == "removed" and event.key == self._array_grouping:
            assert isinstance(event.value, str)
            self._remove_array_from_array_group(array, event.value)
            self._close_if_empty()

    def _add_array_to_array_group(
        self, array: Array, array_group: str, initializing: bool = False
    ) -> None:
        if array_group in self._array_groups:
            self._array_group_arrays[array_group].append(array)
        else:
            index = len(self._array_groups)
            if not initializing:
                self.beginInsertRows(QModelIndex(), index, index)
            self._array_groups.insert(index, array_group)
            self._array_group_arrays[array_group] = [array]
            if not initializing:
                self.endInsertRows()

    def _remove_array_from_array_group(
        self, array: Array, array_group: str, initializing: bool = False
    ) -> None:
        self._array_group_arrays[array_group].remove(array)
        if len(self._array_group_arrays[array_group]) == 0:
            index = self._array_groups.index(array_group)
            if not initializing:
                self.beginRemoveRows(QModelIndex(), index, index)
            del self._array_groups[index]
            del self._array_group_arrays[array_group]
            if not initializing:
                self.endRemoveRows()

    def _get_array_group(self, array: Array) -> str:
        if self._array_grouping is not None:
            return array.array_grouping_groups[self._array_grouping]
        return array.name

    def _close_if_empty(self) -> None:
        if len(self._array_groups) == 0 and self._close_callback is not None:
            self._disconnect_events()
            self._close_callback()

    @property
    def array_groups(self) -> Sequence[str]:
        return self._array_groups

    @property
    def array_group_arrays(self) -> Mapping[str, Sequence[Array]]:
        return self._array_group_arrays
