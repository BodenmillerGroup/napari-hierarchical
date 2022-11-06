from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

from napari.utils.events import Event, EventedDict, EventedList
from qtpy.QtCore import QAbstractListModel, QModelIndex, QObject, Qt

from .._controller import DatasetController
from ..model import Layer
from ..utils.parent_aware import ParentAwareEventedModelDict


class QLayerGroupingListModel(QAbstractListModel):
    def __init__(
        self,
        controller: DatasetController,
        grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._grouping = grouping
        self._close_callback = close_callback
        self._groups: List[str] = []
        self._group_layers: Dict[str, List[Layer]] = {}
        for layer in controller.current_layers:
            if grouping is None or grouping in layer.groups:
                group = self._get_layer_group(layer)
                self._add_layer_to_group(layer, group, initializing=True)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._group_layers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid() and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
        ):
            assert 0 <= index.row() < len(self._groups)
            return self._groups[index.row()]
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            assert 0 <= index.row() < len(self._groups)
            assert isinstance(value, str)
            group = self._groups[index.row()]
            for layer in self._group_layers[group]:
                self._set_layer_group(layer, value)
            return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.isValid():
            assert flags & Qt.ItemFlag.ItemIsEnabled
            assert flags & Qt.ItemFlag.ItemIsSelectable
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        assert section == 0
        if role == Qt.ItemDataRole.DisplayRole:
            return "Layer group"
        return None

    def _connect_events(self) -> None:
        self._controller.current_layers.events.connect(self._on_current_layers_event)
        for layer in self._controller.current_layers:
            self._connect_layer_events(layer)

    def _disconnect_events(self) -> None:
        for layer in self._controller.current_layers:
            self._disconnect_layer_events(layer)
        self._controller.current_layers.events.disconnect(self._on_current_layers_event)

    def _connect_layer_events(self, layer: Layer) -> None:
        if self._grouping is not None:
            layer.groups.events.connect(self._on_layer_groups_event)
        else:
            layer.events.name.connect(self._on_layer_name_event)

    def _disconnect_layer_events(self, layer: Layer) -> None:
        if self._grouping is not None:
            layer.groups.events.disconnect(self._on_layer_groups_event)
        else:
            layer.events.name.disconnect(self._on_layer_name_event)

    def _on_current_layers_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type == "inserted":
            assert isinstance(event.value, Layer)
            if self._grouping is None or self._grouping in event.value.groups:
                group = self._get_layer_group(event.value)
                self._add_layer_to_group(event.value, group)
            self._connect_layer_events(event.value)
        elif event.type == "removed":
            assert isinstance(event.value, Layer)
            self._disconnect_layer_events(event.value)
            if self._grouping is None or self._grouping in event.value.groups:
                group = self._get_layer_group(event.value)
                self._remove_layer_from_group(event.value, group)
                self._close_if_empty()
        elif event.type == "changed" and isinstance(event.index, int):
            close_if_empty = False
            assert isinstance(event.old_value, Layer)
            self._disconnect_layer_events(event.old_value)
            if self._grouping is None or self._grouping in event.old_value.groups:
                old_group = self._get_layer_group(event.old_value)
                self._remove_layer_from_group(event.old_value, old_group)
                close_if_empty = True
            assert isinstance(event.value, Layer)
            if self._grouping is None or self._grouping in event.value.groups:
                group = self._get_layer_group(event.value)
                self._add_layer_to_group(event.value, group)
                close_if_empty = False
            self._connect_layer_events(event.value)
            if close_if_empty:
                self._close_if_empty()
        elif event.type == "changed":
            close_if_empty = False
            assert isinstance(event.old_value, List)
            for old_layer in event.old_value:
                assert isinstance(old_layer, Layer)
                self._disconnect_layer_events(old_layer)
                if self._grouping is None or self._grouping in old_layer.groups:
                    old_group = self._get_layer_group(old_layer)
                    self._remove_layer_from_group(old_layer, old_group)
                    close_if_empty = True
            assert isinstance(event.value, List)
            for layer in event.value:
                assert isinstance(layer, Layer)
                if self._grouping is None or self._grouping in layer.groups:
                    group = self._get_layer_group(layer)
                    self._add_layer_to_group(layer, group)
                    close_if_empty = False
                self._connect_layer_events(layer)
            if close_if_empty:
                self._close_if_empty()

    def _on_layer_name_event(self, event: Event) -> None:
        assert self._grouping is None
        layer = event.source
        assert isinstance(layer, Layer)
        old_group = next(
            group
            for group, layers in self._group_layers.items()
            if event.source in layers
        )
        self._remove_layer_from_group(event.source, old_group)
        group = self._get_layer_group(event.source)
        self._add_layer_to_group(event.source, group)

    def _on_layer_groups_event(self, event: Event) -> None:
        assert self._grouping is not None
        if not isinstance(event.sources[0], EventedDict):
            return
        layer_groups = event.source
        assert isinstance(layer_groups, ParentAwareEventedModelDict)
        layer = layer_groups.get_parent()
        assert isinstance(layer, Layer)
        if event.type == "changed" and event.key == self._grouping:
            assert isinstance(event.old_value, str)
            self._remove_layer_from_group(layer, event.old_value)
            assert isinstance(event.value, str)
            self._add_layer_to_group(layer, event.value)
        elif event.type == "added" and event.key == self._grouping:
            assert isinstance(event.value, str)
            self._add_layer_to_group(layer, event.value)
        elif event.type == "removed" and event.key == self._grouping:
            assert isinstance(event.value, str)
            self._remove_layer_from_group(layer, event.value)
            self._close_if_empty()

    def _add_layer_to_group(
        self, layer: Layer, group: str, initializing: bool = False
    ) -> None:
        if group in self._groups:
            self._group_layers[group].append(layer)
        else:
            index = len(self._groups)
            if not initializing:
                self.beginInsertRows(QModelIndex(), index, index)
            self._groups.insert(index, group)
            self._group_layers[group] = [layer]
            if not initializing:
                self.endInsertRows()

    def _remove_layer_from_group(
        self, layer: Layer, group: str, initializing: bool = False
    ) -> None:
        self._group_layers[group].remove(layer)
        if len(self._group_layers[group]) == 0:
            index = self._groups.index(group)
            if not initializing:
                self.beginRemoveRows(QModelIndex(), index, index)
            del self._groups[index]
            del self._group_layers[group]
            if not initializing:
                self.endRemoveRows()

    def _get_layer_group(self, layer: Layer) -> str:
        if self._grouping is not None:
            return layer.groups[self._grouping]
        return layer.name

    def _set_layer_group(self, layer: Layer, value: str) -> None:
        if self._grouping is not None:
            layer.groups[self._grouping] = value
        layer.name = value

    def _close_if_empty(self) -> None:
        if len(self._groups) == 0 and self._close_callback is not None:
            self._disconnect_events()
            self._close_callback()

    @property
    def groups(self) -> Sequence[str]:
        return self._groups

    @property
    def group_layers(self) -> Mapping[str, Sequence[Layer]]:
        return self._group_layers
