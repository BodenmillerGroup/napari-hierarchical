import logging
from typing import Callable, Optional, Set

from napari.utils.events import Event
from qtpy.QtCore import QItemSelection, QPoint, QSortFilterProxyModel, Qt
from qtpy.QtWidgets import QHeaderView, QMenu, QTreeView, QWidget

from .._controller import HierarchicalController
from ..model import Array
from ._flat_grouping_tree_model import Arrays, QFlatGroupingTreeModel
from .resources import get_pixmap
from .utils import QIconCheckboxDelegate

logger = logging.getLogger(__name__)


class QFlatGroupingTreeView(QTreeView):
    def __init__(
        self,
        controller: HierarchicalController,
        flat_grouping: Optional[str] = None,
        close_callback: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._updating_selection = False
        self._updating_current_arrays_selection = False
        self._model = QFlatGroupingTreeModel(
            controller, flat_grouping=flat_grouping, close_callback=close_callback
        )
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.sort(QFlatGroupingTreeModel.COLUMNS.NAME)
        self.setModel(self._proxy_model)
        self.header().hide()
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            QFlatGroupingTreeModel.COLUMNS.NAME, QHeaderView.ResizeMode.Stretch
        )
        self.header().setSectionResizeMode(
            QFlatGroupingTreeModel.COLUMNS.LOADED,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.header().setSectionResizeMode(
            QFlatGroupingTreeModel.COLUMNS.VISIBLE,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.setItemDelegateForColumn(
            QFlatGroupingTreeModel.COLUMNS.LOADED,
            QIconCheckboxDelegate(
                get_pixmap(":/icons/loaded.svg"),
                get_pixmap(":/icons/loaded_off.svg"),
                get_pixmap(":/icons/loaded_partial.svg"),
                (18, 18),
                self,
            ),
        )
        self.setItemDelegateForColumn(
            QFlatGroupingTreeModel.COLUMNS.VISIBLE,
            QIconCheckboxDelegate(
                get_pixmap(":/icons/visible.svg"),
                get_pixmap(":/icons/visible_off.svg"),
                get_pixmap(":/icons/visible_partial.svg"),
                (18, 18),
                self,
            ),
        )
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_custom_context_menu_requested)
        self.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        # self.setDragDropMode(QTreeView.DragDropMode.DragDrop)
        # self.setDefaultDropAction(Qt.DropAction.MoveAction)
        # self.setDropIndicatorShown(True)
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

    def _on_custom_context_menu_requested(self, pos: QPoint) -> None:
        proxy_index = self.indexAt(pos)
        if proxy_index.isValid():
            index = self._proxy_model.mapToSource(proxy_index)
            if index.isValid():
                array_or_arrays = index.internalPointer()
                assert isinstance(array_or_arrays, (Array, Arrays))
                if isinstance(array_or_arrays, Array):
                    array = array_or_arrays
                    menu = QMenu()
                    load_action = menu.addAction("Load")
                    load_action.setEnabled(
                        not array.loaded and self._controller.can_load_array(array)
                    )
                    unload_action = menu.addAction("Unload")
                    unload_action.setEnabled(
                        array.loaded and self._controller.can_load_array(array)
                    )
                    show_action = menu.addAction("Show")
                    show_action.setEnabled(array.loaded and not array.visible)
                    hide_action = menu.addAction("Hide")
                    hide_action.setEnabled(array.loaded and array.visible)
                    save_action = menu.addAction("Save")
                    save_action.setEnabled(
                        array.loaded and self._controller.can_save_array(array)
                    )
                    remove_action = menu.addAction("Remove")
                    result = menu.exec(self.mapToGlobal(pos))
                    if result == load_action:
                        self._controller.load_array(array)
                    elif result == unload_action:
                        self._controller.unload_array(array)
                    elif result == show_action:
                        array.show()
                    elif result == hide_action:
                        array.hide()
                    elif result == save_action:
                        self._controller.save_array(array)
                    elif result == remove_action:
                        if array.loaded:
                            self._controller.unload_array(array)
                        assert array.layer is None
                        assert array.parent is not None
                        array.parent.arrays.remove(array)
                else:
                    arrays = array_or_arrays
                    menu = QMenu()
                    load_action = menu.addAction("Load")
                    load_action.setEnabled(
                        any(not array.loaded for array in arrays)
                        and all(
                            self._controller.can_load_array(array)
                            for array in arrays
                            if not array.loaded
                        )
                    )
                    unload_action = menu.addAction("Unload")
                    unload_action.setEnabled(
                        any(array.loaded for array in arrays)
                        and all(
                            self._controller.can_load_array(array)
                            for array in arrays
                            if array.loaded
                        )
                    )
                    show_action = menu.addAction("Show")
                    show_action.setEnabled(
                        any(not array.visible for array in arrays if array.loaded)
                    )
                    hide_action = menu.addAction("Hide")
                    hide_action.setEnabled(
                        any(array.visible for array in arrays if array.loaded)
                    )
                    save_action = menu.addAction("Save")
                    save_action.setEnabled(
                        any(array.loaded for array in arrays)
                        and all(
                            self._controller.can_save_array(array)
                            for array in arrays
                            if array.loaded
                        )
                    )
                    remove_action = menu.addAction("Remove")
                    result = menu.exec(self.mapToGlobal(pos))
                    if result == load_action:
                        for array in arrays:
                            if not array.loaded:
                                self._controller.load_array(array)
                    elif result == unload_action:
                        for array in arrays:
                            if array.loaded:
                                self._controller.unload_array(array)
                    elif result == show_action:
                        for array in arrays:
                            if array.loaded and not array.visible:
                                array.show()
                    elif result == hide_action:
                        for array in arrays:
                            if array.loaded and array.visible:
                                array.hide()
                    elif result == save_action:
                        for array in arrays:
                            if array.loaded:
                                self._controller.save_array(array)
                    elif result == remove_action:
                        for array in arrays:
                            if array.loaded:
                                self._controller.unload_array(array)
                            assert array.layer is None
                            assert array.parent is not None
                            array.parent.arrays.remove(array)

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._updating_selection:
            logger.debug(
                f"selected={selected.count()}, deselected={deselected.count()}"
            )
            new_current_arrays_selection: Set[Array] = set()
            selection = self.selectionModel().selection()
            selection = self._proxy_model.mapSelectionToSource(selection)
            for index in selection.indexes():
                if index.column() == 0:
                    array_or_arrays = index.internalPointer()
                    assert isinstance(array_or_arrays, (Array, Arrays))
                    if isinstance(array_or_arrays, Array):
                        array = array_or_arrays
                        new_current_arrays_selection.add(array)
                    else:
                        arrays = array_or_arrays
                        new_current_arrays_selection.update(arrays)
            self._updating_current_arrays_selection = True
            try:
                self._controller.current_arrays.selection = new_current_arrays_selection
            finally:
                self._updating_current_arrays_selection = False

    def _on_current_arrays_selection_changed_event(self, event: Event) -> None:
        if not self._updating_current_arrays_selection and not self._model.dropping:
            # new_selection = QItemSelection()
            # for array in self._controller.current_arrays.selection:
            #     if self._model.flat_grouping is None:
            #         index = self._model.create_flat_group_index(array.name)
            #         new_selection.append(QItemSelectionRange(index))
            #     elif self._model.flat_grouping in array.flat_grouping_groups:
            #         flat_group = array.flat_grouping_groups[self._model.flat_grouping]
            #         index = self._model.create_flat_group_index(flat_group)
            #         new_selection.append(QItemSelectionRange(index))
            # new_selection = self._proxy_model.mapSelectionFromSource(new_selection)
            logger.debug("")
            self._updating_selection = True
            try:
                self.selectionModel().clear()  # TODO select arrays
                # self.selectionModel().select(
                #     new_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect
                # )
            finally:
                self._updating_selection = False
