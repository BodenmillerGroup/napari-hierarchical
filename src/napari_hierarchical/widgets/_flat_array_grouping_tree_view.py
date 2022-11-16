from typing import Callable, Optional, Set

from napari.utils.events import Event
from qtpy.QtCore import QItemSelection, QSortFilterProxyModel
from qtpy.QtWidgets import QHeaderView, QTreeView, QWidget

from .._controller import HierarchicalController
from ..model import Array
from ._flat_array_grouping_tree_model import QFlatArrayGroupingTreeModel


# TODO styling (checkboxes)
class QFlatArrayGroupingTreeView(QTreeView):
    def __init__(
        self,
        controller: HierarchicalController,
        flat_grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._model = QFlatArrayGroupingTreeModel(
            controller, flat_grouping=flat_grouping, close_callback=close_callback
        )
        self._updating_selection = False
        self._updating_current_arrays_selection = False
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.sort(QFlatArrayGroupingTreeModel.COLUMNS.NAME)
        self.setModel(self._proxy_model)
        self.header().hide()
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            QFlatArrayGroupingTreeModel.COLUMNS.NAME, QHeaderView.ResizeMode.Stretch
        )
        self.header().setSectionResizeMode(
            QFlatArrayGroupingTreeModel.COLUMNS.LOADED,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.header().setSectionResizeMode(
            QFlatArrayGroupingTreeModel.COLUMNS.VISIBLE,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeView.DragDropMode.DragDrop)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.current_arrays.selection.events.changed.connect(
            self._on_current_arrays_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        self._controller.current_arrays.selection.events.changed.disconnect(
            self._on_current_arrays_selection_changed_event
        )

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._updating_selection:
            new_current_arrays_selection: Set[Array] = set()
            for proxy_index in self.selectionModel().selectedRows():
                index = self._proxy_model.mapToSource(proxy_index)
                array_or_flat_group = index.internalPointer()
                if isinstance(array_or_flat_group, Array):
                    array = array_or_flat_group
                    new_current_arrays_selection.add(array)
                elif isinstance(array_or_flat_group, str):
                    flat_group = array_or_flat_group
                    arrays = self._model.flat_group_arrays[flat_group]
                    new_current_arrays_selection.update(arrays)
            self._updating_current_arrays_selection = True
            try:
                self._controller.current_arrays.selection = new_current_arrays_selection
            finally:
                self._updating_current_arrays_selection = False

    def _on_current_arrays_selection_changed_event(self, event: Event) -> None:
        if not self._updating_current_arrays_selection:
            # new_item_selection = QItemSelection()
            # for array in self._controller.current_arrays.selection:
            #     if (
            #         self._model.flat_grouping is None
            #         or self._model.flat_grouping in array.flat_grouping_groups
            #     ):
            #         index = self._model.create_index_for_array(array)
            #         proxy_index = self._proxy_model.mapFromSource(index)
            #         new_item_selection.append(QItemSelectionRange(proxy_index))
            self._updating_selection = True
            try:
                self.selectionModel().clear()  # TODO select arrays
                # self.selectionModel().select(
                #     new_item_selection,
                #     QItemSelectionModel.SelectionFlag.ClearAndSelect,
                # )
            finally:
                self._updating_selection = False

    # TODO context menu (save arrays)
