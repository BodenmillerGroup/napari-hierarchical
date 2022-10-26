from typing import Any, Callable, Dict, List, Optional

from napari.utils.events import Event, EventedDict, EventedList
from qtpy.QtCore import QAbstractTableModel, QModelIndex, QObject, Qt

from .._controller import BioImageController
from ..model import EventedLayerGroupsDict, Layer


class QLayerGroupingModel(QAbstractTableModel):
    def __init__(
        self,
        controller: BioImageController,
        grouping: str,
        close_callback: Callable[[], None],
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._grouping = grouping
        self._close_callback = close_callback
        self._groups: List[str] = []
        self._group_layers: Dict[str, List[Layer]] = {}
        for layer in controller.layers:
            if grouping in layer.groups:
                group = layer.groups[grouping]
                if group in self._groups:
                    self._group_layers[group].append(layer)
                else:
                    index = len(self._groups)
                    self._groups.insert(index, group)
                    self._group_layers[group] = [layer]
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self._group_layers)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid() and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
        ):
            assert 0 <= index.row() < len(self._groups)
            assert index.column() == 0
            return self._groups[index.row()]
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            assert 0 <= index.row() < len(self._groups)
            assert index.column() == 0
            group = self._groups[index.row()]
            for layer in self._group_layers[group]:
                layer.groups[self._grouping] = group
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
        if section == 0 and role == Qt.ItemDataRole.DisplayRole:
            return "Layer group"
        return None

    def _connect_events(self) -> None:
        self._controller.layers.events.connect(self._on_layers_event)
        for layer in self._controller.layers:
            self._connect_layer_events(layer)

    def _disconnect_events(self) -> None:
        for layer in self._controller.layers:
            self._disconnect_layer_events(layer)
        self._controller.layers.events.disconnect(self._on_layers_event)

    def _connect_layer_events(self, layer: Layer) -> None:
        layer.groups.events.connect(self._on_layer_groups_event)

    def _disconnect_layer_events(self, layer: Layer) -> None:
        layer.groups.events.disconnect(self._on_layer_groups_event)

    def _on_layers_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type == "inserted":
            assert isinstance(event.value, Layer)
            if self._grouping in event.value.groups:
                group = event.value.groups[self._grouping]
                self._add_layer_to_group(event.value, group)
            self._connect_layer_events(event.value)
        elif event.type == "removed":
            assert isinstance(event.value, Layer)
            self._disconnect_layer_events(event.value)
            if self._grouping in event.value.groups:
                group = event.value.groups[self._grouping]
                self._remove_layer_from_group(event.value, group)
        elif event.type == "changed" and isinstance(event.index, int):
            assert isinstance(event.old_value, Layer)
            self._disconnect_layer_events(event.old_value)
            if self._grouping in event.old_value.groups:
                group = event.old_value.groups[self._grouping]
                self._remove_layer_from_group(event.old_value, group)
            assert isinstance(event.value, Layer)
            if self._grouping in event.value.groups:
                group = event.value.groups[self._grouping]
                self._add_layer_to_group(event.value, group)
            self._connect_layer_events(event.value)
        elif event.type == "changed" and isinstance(event.index, slice):
            assert isinstance(event.old_value, List)
            for old_layer in event.old_value:
                assert isinstance(old_layer, Layer)
                self._disconnect_layer_events(old_layer)
                if self._grouping in old_layer.groups:
                    group = old_layer.groups[self._grouping]
                    self._remove_layer_from_group(old_layer, group)
            assert isinstance(event.value, List)
            for layer in event.value:
                assert isinstance(layer, Layer)
                if self._grouping in layer.groups:
                    group = layer.groups[self._grouping]
                    self._add_layer_to_group(layer, group)
                self._connect_layer_events(layer)

    def _on_layer_groups_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedDict):
            return
        assert isinstance(event.source, EventedLayerGroupsDict)
        layer = event.source.layer
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

    def _add_layer_to_group(self, layer: Layer, group: str) -> None:
        if group in self._groups:
            self._group_layers[group].append(layer)
        else:
            index = len(self._groups)
            self.beginInsertRows(QModelIndex(), index, index)
            self._groups.insert(index, group)
            self._group_layers[group] = [layer]
            self.endInsertRows()

    def _remove_layer_from_group(self, layer: Layer, group: str) -> None:
        self._group_layers[group].remove(layer)
        if len(self._group_layers[group]) == 0:
            index = self._groups.index(group)
            self.beginRemoveRows(QModelIndex(), index, index)
            del self._groups[index]
            del self._group_layers[group]
            self.endRemoveRows()
            if len(self._group_layers) == 0:
                self._close_callback()
