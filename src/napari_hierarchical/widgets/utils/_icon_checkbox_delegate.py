from typing import Optional, Tuple

from qtpy.QtCore import QModelIndex, QObject, QSize, Qt
from qtpy.QtGui import QIcon, QPainter, QPixmap
from qtpy.QtWidgets import (
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionViewItem,
)


class QIconCheckboxDelegate(QStyledItemDelegate):
    def __init__(
        self,
        checked_pixmap: QPixmap,
        unchecked_pixmap: QPixmap,
        partially_checked_pixmap: QPixmap,
        icon_size: Tuple[int, int],
        parent: Optional[QObject],
    ) -> None:
        super().__init__(parent)
        self._checked_icon = QIcon(checked_pixmap)
        self._unchecked_icon = QIcon(unchecked_pixmap)
        self._partially_checked_icon = QIcon(partially_checked_pixmap)
        self._icon_size = icon_size

    def paint(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ) -> None:
        self.initStyleOption(option, index)
        button_option = QStyleOptionButton()
        button_option.initFrom(option.widget)
        button_option.rect = option.rect
        button_option.state |= QStyle.StateFlag.State_Enabled
        check_state = index.data(role=Qt.ItemDataRole.CheckStateRole)
        if check_state == Qt.CheckState.Checked:
            button_option.state |= QStyle.StateFlag.State_On
            button_option.icon = self._checked_icon
        elif check_state == Qt.CheckState.Unchecked:
            button_option.state |= QStyle.StateFlag.State_Off
            button_option.icon = self._unchecked_icon
        elif check_state == Qt.CheckState.PartiallyChecked:
            button_option.state |= QStyle.StateFlag.State_NoChange
            button_option.icon = self._partially_checked_icon
        button_option.iconSize = QSize(*self._icon_size)
        option.widget.style().drawControl(
            QStyle.ControlElement.CE_PushButton, button_option, painter
        )
