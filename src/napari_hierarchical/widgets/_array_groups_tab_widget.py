from typing import Dict, List, Optional

from napari.utils.events import Event
from qtpy.QtWidgets import QTabWidget, QWidget

from .._controller import HierarchicalController
from ..model import Array
from ._array_group_table_view import QArrayGroupTableView


class QArrayGroupsTabWidget(QTabWidget):
    def __init__(
        self, controller: HierarchicalController, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._array_group_table_views: Dict[str, QArrayGroupTableView] = {}
        assert controller.viewer is not None
        self.addTab(QArrayGroupTableView(controller), "Array")
        for array in controller.current_arrays:
            self._register_array(array)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.current_arrays.events.inserted.connect(
            self._on_current_arrays_inserted_event
        )
        self._controller.current_arrays.events.changed.connect(
            self._on_current_arrays_changed_event
        )

    def _disconnect_events(self) -> None:
        self._controller.current_arrays.events.inserted.disconnect(
            self._on_current_arrays_inserted_event
        )
        self._controller.current_arrays.events.changed.disconnect(
            self._on_current_arrays_changed_event
        )

    def _on_current_arrays_inserted_event(self, event: Event) -> None:
        assert isinstance(event.value, Array)
        self._register_array(event.value)

    def _on_current_arrays_changed_event(self, event: Event) -> None:
        if isinstance(event.value, Array):
            self._register_array(event.value)
        else:
            assert isinstance(event.value, List)
            for array in event.value:
                assert isinstance(array, Array)
                self._register_array(array)

    def _register_array(self, array: Array) -> None:
        for array_grouping in array.array_grouping_groups.keys():
            if array_grouping not in self._array_group_table_views:
                array_group_table_view = QArrayGroupTableView(
                    self._controller,
                    array_grouping=array_grouping,
                    close_callback=lambda: self._close_grouping(array_grouping),
                )
                self.addTab(array_group_table_view, array_grouping)
                self._array_group_table_views[array_grouping] = array_group_table_view

    def _close_grouping(self, array_grouping: str) -> None:
        array_group_table_view = self._array_group_table_views.pop(array_grouping)
        array_group_table_view_tab_index = self.indexOf(array_group_table_view)
        self.removeTab(array_group_table_view_tab_index)
