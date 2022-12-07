import logging
from typing import Optional, Set

from napari.utils.events import Event, EventedList
from qtpy.QtCore import QItemSelection, QItemSelectionModel, QItemSelectionRange, Qt
from qtpy.QtWidgets import QHeaderView, QTreeView, QWidget

from .._controller import HierarchicalController
from ..model import Group
from ._group_tree_model import QGroupTreeModel

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

    # TODO context menu (write/save group)
