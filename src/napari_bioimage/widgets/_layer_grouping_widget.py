from typing import Optional, Union

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget

from ..model import Layer


class QLayerGroupingWidget(QWidget):
    def __init__(
        self,
        grouping: Optional[str] = None,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        self._grouping = grouping
        # self._group_layer_lists: Dict[str, List[Layer]] = {}

    def add_layer(self, layer: Layer, group: Optional[str] = None) -> None:
        # if group is None:
        #     group = layer.groups[self._grouping]
        # group_layer_list = self._group_layer_lists.get(group)
        # if group_layer_list is None:
        #     group_layer_list = []
        #     self._group_layer_lists[group] = group_layer_list
        # group_layer_list.append(layer)
        pass

    def update_layer(
        self, layer: Layer, old_group_value: str, new_group: Optional[str] = None
    ) -> None:
        # old_group_layer_list = self._group_layer_lists[old_group_value]
        # old_group_layer_list.remove(layer)
        # # TODO remove entry if necessary
        # if new_group is None:
        #     new_group = layer.groups[self._grouping]
        # new_group_layer_list = self._group_layer_lists.get(new_group)
        # if new_group_layer_list is None:
        #     new_group_layer_list = []
        #     self._group_layer_lists[new_group] = new_group_layer_list
        # new_group_layer_list.append(layer)
        pass

    def remove_layer(self, layer: Layer, group: Optional[str] = None) -> None:
        # if group is None:
        #     group = layer.groups[self._grouping]
        # group_layer_list = self._group_layer_lists[group]
        # group_layer_list.remove(layer)
        # # TODO remove entry if necessary
        pass
