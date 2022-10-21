from typing import Any, NamedTuple, Optional

from napari.utils.events import Event
from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt

from .._controller import BioImageController
from ..model import Image, ImageGroup


class QImageTreeModel(QAbstractItemModel):
    class Column(NamedTuple):
        field: str
        title: str
        editable: bool

    COLUMNS = [
        Column("name", "Image", True),
    ]

    def __init__(
        self, controller: BioImageController, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._controller = controller
        self._controller.images.events.connect(self._on_images_changed)

    def __del__(self) -> None:
        self._controller.images.events.disconnect(self._on_images_changed)

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if 0 <= column < len(self.COLUMNS):
            if parent.isValid():
                parent_image_group = parent.internalPointer()
                assert isinstance(parent_image_group, ImageGroup)
                if 0 <= row < len(parent_image_group.children):
                    image = parent_image_group.children[row]
                    return self.createIndex(row, column, object=image)
            elif 0 <= row < len(self._controller.images):
                image = self._controller.images[row]
                return self.createIndex(row, column, object=image)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if index.isValid():
            image = index.internalPointer()
            assert isinstance(image, Image)
            if image.parent is not None:
                if image.parent.parent is not None:
                    row = image.parent.parent.children.index(image.parent)
                else:
                    row = self._controller.images.index(image.parent)
                return self.createIndex(row, 0, object=image.parent)
        return QModelIndex()

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        if index.isValid():
            image = index.internalPointer()
            if isinstance(image, ImageGroup):
                return len(image.children)
            return 0
        return len(self._controller.images)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.isValid() and 0 <= index.column() < len(self.COLUMNS):
            column = self.COLUMNS[index.column()]
            if column.editable:
                flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and 0 <= section < len(self.COLUMNS):
            column = self.COLUMNS[section]
            return column.title
        return None

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        image_parent = None
        images = self._controller.images
        if parent.isValid():
            parent_image = parent.internalPointer()
            assert isinstance(parent_image, Image)
            if isinstance(parent_image, ImageGroup):
                images = parent_image.children
                image_parent = parent_image
            elif parent_image.parent is not None:
                images = parent_image.parent.children
                image_parent = parent_image.parent
        if 0 <= row < row + count <= len(images):
            self.beginInsertRows(parent, row, row + count - 1)
            for i in range(row, row + count):
                image = Image(name="New Image", parent=image_parent)
                images.insert(i, image)
            self.endInsertRows()
            return True
        return False

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        images = self._controller.images
        if parent.isValid():
            parent_image = parent.internalPointer()
            assert isinstance(parent_image, Image)
            if isinstance(parent_image, ImageGroup):
                images = parent_image.children
            elif parent_image.parent is not None:
                images = parent_image.parent.children
        if 0 <= row < row + count <= len(images):
            self.beginRemoveRows(parent, row, row + count - 1)
            del images[row : row + count]
            self.endRemoveRows()
            return True
        return False

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if (
            index.isValid()
            and 0 <= index.column() < len(self.COLUMNS)
            and role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole)
        ):
            image = index.internalPointer()
            assert isinstance(image, Image)
            column = self.COLUMNS[index.column()]
            return getattr(image, column.field)
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if (
            index.isValid()
            and 0 <= index.column() < len(self.COLUMNS)
            and role == Qt.ItemDataRole.EditRole
        ):
            image = index.internalPointer()
            assert isinstance(image, Image)
            column = self.COLUMNS[index.column()]
            setattr(image, column.field, value)
            return True
        return False

    def _on_images_changed(
        self, event: Event, image_group: Optional[ImageGroup] = None
    ) -> None:
        # EventedList instances catch events of their EventedModel items
        if isinstance(event.sources[0], Image):
            return self._on_image_changed(event, event.sources[0])

        def parent_index():
            if image_group is not None:
                if image_group.parent is not None:
                    row = image_group.parent.children.index(image_group)
                else:
                    row = self._controller.images.index(image_group)
                return self.createIndex(row, 0, object=image_group)
            return QModelIndex()

        # event.sources does not seem to work for nested EventedLists
        if image_group is not None:
            images = image_group.children
        else:
            images = self._controller.images

        if event.type == "inserting":
            assert isinstance(event.index, int) and 0 <= event.index <= len(images)
            self.beginInsertRows(parent_index(), event.index, event.index)
        elif event.type == "inserted":
            if isinstance(event.value, ImageGroup):
                event.value._callback = event.value.children.events.connect(
                    lambda e: self._on_images_changed(e, image_group=event.value)
                )
            self.endInsertRows()
        elif event.type == "removing":
            assert isinstance(event.index, int) and 0 <= event.index < len(images)
            self.beginRemoveRows(parent_index(), event.index, event.index)
        elif event.type == "removed":
            if isinstance(event.value, ImageGroup):
                event.value.children.events.disconnect(event.value._callback)
            self.endRemoveRows()
        elif event.type == "moving":
            assert isinstance(event.index, int) and 0 <= event.index < len(images)
            assert (
                isinstance(event.new_index, int)
                and 0 <= event.new_index <= len(images)
                and event.new_index != event.index
            )
            parent = parent_index()
            self.beginMoveRows(
                parent, event.index, event.index, parent, event.new_index
            )
        elif event.type == "moved":
            self.endMoveRows()
        elif event.type == "changed" and isinstance(event.index, int):
            assert 0 <= event.index < len(images)
            left_index = self.createIndex(event.index, 0, object=images[event.index])
            right_index = self.createIndex(
                event.index, len(self.COLUMNS) - 1, object=images[event.index]
            )
            self.dataChanged.emit(left_index, right_index)
        elif event.type in ("changed", "reordered"):
            top_left_index = self.createIndex(0, 0, object=images[0])
            bottom_right_index = self.createIndex(
                len(images) - 1, len(self.COLUMNS) - 1, object=images[-1]
            )
            self.dataChanged.emit(top_left_index, bottom_right_index)

    def _on_image_changed(self, event: Event, image: Image) -> None:
        column_index = next(
            (i for i, c in enumerate(self.COLUMNS) if c.field == event.type), None
        )
        if column_index is not None:
            if image.parent is not None:
                row = image.parent.children.index(image)
            else:
                row = self._controller.images.index(image)
            index = self.createIndex(row, column_index, object=image)
            self.dataChanged.emit(index, index)
