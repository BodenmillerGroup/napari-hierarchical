import logging
from typing import Dict, List, Optional

from napari.utils.events import Event
from qtpy.QtWidgets import QTabWidget, QWidget

from .._controller import HierarchicalController
from ..model import Array
from ._flat_grouping_tree_view import QFlatGroupingTreeView

logger = logging.getLogger(__name__)


class QFlatGroupingsTabWidget(QTabWidget):
    def __init__(
        self, controller: HierarchicalController, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._flat_grouping_tree_views: Dict[str, QFlatGroupingTreeView] = {}
        assert controller.viewer is not None
        self.addTab(QFlatGroupingTreeView(controller), "Array")
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
        logger.debug(f"event={event.type}")
        array = event.value
        assert isinstance(array, Array)
        self._register_array(array)

    def _on_current_arrays_changed_event(self, event: Event) -> None:
        logger.debug("")
        array_or_arrays = event.value
        if isinstance(array_or_arrays, Array):
            array = array_or_arrays
            self._register_array(array)
        else:
            arrays = array_or_arrays
            assert isinstance(arrays, List)
            for array in arrays:
                assert isinstance(array, Array)
                self._register_array(array)

    def _register_array(self, array: Array) -> None:
        for flat_grouping in array.flat_grouping_groups.keys():
            if flat_grouping not in self._flat_grouping_tree_views:
                logger.debug(f"array={array}")
                flat_grouping_tree_view = QFlatGroupingTreeView(
                    self._controller,
                    flat_grouping=flat_grouping,
                    close_callback=lambda: self._close_tab(flat_grouping),
                )
                self.addTab(flat_grouping_tree_view, flat_grouping)
                self._flat_grouping_tree_views[flat_grouping] = flat_grouping_tree_view

    def _close_tab(self, flat_grouping: str) -> None:
        logger.debug(f"flat_grouping={flat_grouping}")
        flat_grouping_tree_view = self._flat_grouping_tree_views.pop(flat_grouping)
        tab_index = self.indexOf(flat_grouping_tree_view)
        self.removeTab(tab_index)
