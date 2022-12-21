import logging
from typing import Optional, Set

from napari.utils.events import Event, EventedList
from qtpy.QtCore import (
    QItemSelection,
    QItemSelectionModel,
    QItemSelectionRange,
    QPoint,
    Qt,
)
from qtpy.QtWidgets import QFileDialog, QHeaderView, QMenu, QTreeView, QWidget

from .._controller import HierarchicalController
from ..model import Group
from ._group_tree_model import QGroupTreeModel
from .resources import get_pixmap
from .utils import QIconCheckboxDelegate

logger = logging.getLogger(__name__)


class QGroupTreeView(QTreeView):
    def __init__(
        self, controller: HierarchicalController, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._updating_selection = False
        self._updating_selected_groups = False
        self._model = QGroupTreeModel(controller)
        self.setModel(self._model)
        self.header().hide()
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            QGroupTreeModel.COLUMNS.NAME, QHeaderView.ResizeMode.Stretch
        )
        self.header().setSectionResizeMode(
            QGroupTreeModel.COLUMNS.LOADED, QHeaderView.ResizeMode.ResizeToContents
        )
        self.header().setSectionResizeMode(
            QGroupTreeModel.COLUMNS.VISIBLE, QHeaderView.ResizeMode.ResizeToContents
        )
        self.setItemDelegateForColumn(
            QGroupTreeModel.COLUMNS.LOADED,
            QIconCheckboxDelegate(
                get_pixmap(":/icons/loaded.svg"),
                get_pixmap(":/icons/loaded_off.svg"),
                get_pixmap(":/icons/loaded_partial.svg"),
                (18, 18),
                self,
            ),
        )
        self.setItemDelegateForColumn(
            QGroupTreeModel.COLUMNS.VISIBLE,
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
        self.setDragDropMode(QTreeView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDropIndicatorShown(True)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._controller.selected_groups.events.connect(self._on_selected_groups_event)

    def _disconnect_events(self) -> None:
        self._controller.selected_groups.events.disconnect(
            self._on_selected_groups_event
        )

    def _on_custom_context_menu_requested(self, pos: QPoint) -> None:
        index = self.indexAt(pos)
        if index.isValid():
            group = index.internalPointer()
            assert isinstance(group, Group)
            menu = QMenu()
            remove_action = menu.addAction("Remove")
            if group.parent is None:
                export_action = menu.addAction("Export")
                export_action.setEnabled(group.loaded is not None and group.loaded)
            else:
                export_action = None
            menu.addSeparator()
            load_arrays_action = menu.addAction("Load arrays")
            load_arrays_action.setEnabled(
                group.loaded in (None, False)
                and self._controller.can_load_group(group, unloaded_only=True)
            )
            unload_arrays_action = menu.addAction("Unload arrays")
            unload_arrays_action.setEnabled(
                group.loaded in (None, True)
                and self._controller.can_load_group(group, loaded_only=True)
            )
            show_arrays_action = menu.addAction("Show arrays")
            show_arrays_action.setEnabled(
                group.loaded in (None, True) and group.visible in (None, False)
            )
            hide_arrays_action = menu.addAction("Hide arrays")
            hide_arrays_action.setEnabled(
                group.loaded in (None, True) and group.visible in (None, True)
            )
            save_arrays_action = menu.addAction("Save arrays")
            save_arrays_action.setEnabled(
                group.loaded in (None, True) and self._controller.can_save_group(group)
            )
            result = menu.exec(self.mapToGlobal(pos))
            if export_action is not None and result == export_action:
                path, _ = QFileDialog.getSaveFileName()
                if path:
                    self._controller.write_group(path, group)
            elif result == remove_action:
                if group.loaded in (None, True):
                    self._controller.unload_group(group)
                assert all(
                    array.layer is None for array in group.iter_arrays(recursive=True)
                )
                if group.parent is not None:
                    group.parent.children.remove(group)
                else:
                    self._controller.groups.remove(group)
            elif result == load_arrays_action:
                self._controller.load_group(group)
            elif result == unload_arrays_action:
                self._controller.unload_group(group)
            elif result == show_arrays_action:
                group.show()
            elif result == hide_arrays_action:
                group.hide()
            elif result == save_arrays_action:
                self._controller.save_group(group)

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        if not self._updating_selection:
            logger.debug(
                f"selected={selected.count()}, deselected={deselected.count()}"
            )
            old_selected_groups = set(self._controller.selected_groups)
            new_selected_groups: Set[Group] = set()
            for index in self.selectionModel().selectedRows():
                group = index.internalPointer()
                assert isinstance(group, Group)
                new_selected_groups.add(group)
            self._updating_selected_groups = True
            try:
                for group in old_selected_groups.difference(new_selected_groups):
                    self._controller.selected_groups.remove(group)
                for group in new_selected_groups.difference(old_selected_groups):
                    self._controller.selected_groups.append(group)
            finally:
                self._updating_selected_groups = False

    def _on_selected_groups_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if (
            event.type in ("inserted", "removed", "changed")
            and not self._updating_selected_groups
            and not self._model.dropping
        ):
            logger.debug(f"event={event.type}")
            new_selection = QItemSelection()
            for group in self._controller.selected_groups:
                index = self._model.create_group_index(group)
                new_selection.append(QItemSelectionRange(index))
            self._updating_selection = True
            try:
                self.selectionModel().select(
                    new_selection, QItemSelectionModel.SelectionFlag.ClearAndSelect
                )
            finally:
                self._updating_selection = False
