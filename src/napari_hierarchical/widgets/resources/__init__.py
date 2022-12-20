from qtpy.QtGui import QPixmap

from .resources import qInitResources

qInitResources()


def get_pixmap(file_name: str) -> QPixmap:
    return QPixmap(file_name)
