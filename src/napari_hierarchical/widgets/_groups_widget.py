import logging
from typing import Optional, Union

from napari.utils.events import Event, EventedList
from napari.viewer import Viewer
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .._controller import controller
from ..model import Group
from ._group_tree_view import QGroupTreeView

logger = logging.getLogger(__name__)


def _get_group_level(group: Group, current_level: int = 0) -> int:
    if group.parent is not None:
        current_level += 1
        return _get_group_level(group.parent, current_level=current_level)
    return current_level


class QGroupsWidget(QWidget):
    def __init__(
        self,
        napari_viewer: Viewer,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        if controller.viewer != napari_viewer:
            controller.register_viewer(napari_viewer)
        self._new_group_push_button = QPushButton("New")
        self._new_group_push_button.clicked.connect(
            self._on_new_group_push_button_clicked
        )
        self._delete_group_push_button = QPushButton("Delete")
        self._delete_group_push_button.clicked.connect(
            self._on_delete_group_push_button_clicked
        )
        self._group_tool_bar = QToolBar("Groups")
        self._group_tool_bar.addWidget(QLabel("Groups"))
        group_tool_bar_spacer = QWidget()
        group_tool_bar_spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._group_tool_bar.addWidget(group_tool_bar_spacer)
        self._group_tool_bar.addWidget(self._new_group_push_button)
        self._group_tool_bar.addWidget(self._delete_group_push_button)
        self._group_tree_view = QGroupTreeView(controller)
        self._init_layout()
        self._connect_events()
        self._update_delete_group_push_button_enabled()

    def __del__(self) -> None:
        self._disconnect_events()

    def _init_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._group_tool_bar)
        layout.addWidget(self._group_tree_view)
        self.setLayout(layout)

    def _connect_events(self) -> None:
        controller.selected_groups.events.connect(self._on_selected_groups_event)

    def _disconnect_events(self) -> None:
        controller.selected_groups.events.disconnect(self._on_selected_groups_event)

    def _on_selected_groups_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type in ("inserted", "removed", "changed"):
            logger.debug(f"event={event.type}")
            self._update_delete_group_push_button_enabled()

    def _on_new_group_push_button_clicked(self, checked: bool = False) -> None:
        logger.debug(f"checked={checked}")
        if len(controller.selected_groups) == 1:
            groups = controller.selected_groups[0].children
        else:
            groups = controller.groups
        group = Group(name="New Group")
        groups.append(group)
        controller.selected_groups.clear()
        controller.selected_groups.append(group)

    def _on_delete_group_push_button_clicked(self, checked: bool = False) -> None:
        logger.debug(f"checked={checked}")
        groups = sorted(controller.selected_groups, key=_get_group_level, reverse=True)
        controller.selected_groups.clear()
        for group in groups:
            if group.loaded in (None, True):
                controller.unload_group(group)
            assert all(
                array.layer is None for array in group.iter_arrays(recursive=True)
            )
            if group.parent is not None:
                group.parent.children.remove(group)
            else:
                controller.groups.remove(group)

    def _update_delete_group_push_button_enabled(self) -> None:
        enabled = len(controller.selected_groups) > 0
        logger.debug(f"enabled={enabled}")
        self._delete_group_push_button.setEnabled(enabled)
