import pickle
from contextlib import contextmanager
from typing import Any, Iterable, List, NamedTuple, Optional

from napari.utils.events import Event
from qtpy.QtCore import QAbstractItemModel, QMimeData, QModelIndex, QObject, Qt

from .._controller import BioImageController
from ..model import Image


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
        self._ignore_images_changed = False
        self._controller.images.events.connect(self._on_images_changed)
        for image in self._controller.images:
            self._connect_image(image)

    def __del__(self) -> None:
        for image in self._controller.images:
            self._disconnect_image(image)
        self._controller.images.events.disconnect(self._on_images_changed)

    @contextmanager
    def ignore_images_changed(self):
        assert not self._ignore_images_changed
        self._ignore_images_changed = True
        yield
        self._ignore_images_changed = False

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if 0 <= column < len(self.COLUMNS):
            if parent.isValid():
                parent_image = parent.internalPointer()
                assert isinstance(parent_image, Image)
                if 0 <= row < len(parent_image.children):
                    image = parent_image.children[row]
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
            assert isinstance(image, Image)
            return len(image.children)
        return len(self._controller.images)

    def columnCount(self, index: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        if index.isValid():
            assert flags & Qt.ItemFlag.ItemIsEnabled
            assert flags & Qt.ItemFlag.ItemIsSelectable
            assert 0 <= index.column() < len(self.COLUMNS)
            column = self.COLUMNS[index.column()]
            if column.editable:
                flags |= Qt.ItemFlag.ItemIsEditable
            flags |= Qt.ItemFlag.ItemIsDragEnabled
        flags |= Qt.ItemFlag.ItemIsDropEnabled
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

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if index.isValid() and role in (
            Qt.ItemDataRole.DisplayRole,
            Qt.ItemDataRole.EditRole,
        ):
            image = index.internalPointer()
            assert isinstance(image, Image)
            assert 0 <= index.column() < len(self.COLUMNS)
            column = self.COLUMNS[index.column()]
            return getattr(image, column.field)
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            image = index.internalPointer()
            assert isinstance(image, Image)
            assert 0 <= index.column() < len(self.COLUMNS)
            column = self.COLUMNS[index.column()]
            with self.ignore_images_changed():
                setattr(image, column.field, value)
                self.dataChanged.emit(index, index)
            return True
        return False

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if parent.isValid():
            parent_image = parent.internalPointer()
            assert isinstance(parent_image, Image)
            images = parent_image.children
        else:
            parent_image = None
            images = self._controller.images
        if 0 <= row <= len(images) and count > 0:
            with self.ignore_images_changed():
                self.beginInsertRows(parent, row, row + count - 1)
                for i in range(row, row + count):
                    image = Image(name="New Image", parent=parent_image)
                    images.insert(i, image)
                self.endInsertRows()
            return True
        return False

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        if parent.isValid():
            parent_image = parent.internalPointer()
            assert isinstance(parent_image, Image)
            images = parent_image.children
        else:
            images = self._controller.images
        if 0 <= row < row + count <= len(images) and count > 0:
            with self.ignore_images_changed():
                self.beginRemoveRows(parent, row, row + count - 1)
                del images[row : row + count]
                self.endRemoveRows()
            return True
        return False

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeTypes(self) -> List[str]:
        mime_types = super().mimeTypes()
        mime_types.append("x-napari-bioimage")
        return mime_types

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        data = super().mimeData(indexes)
        indices_stacks = []
        for index in indexes:
            indices_stack = []
            while index.isValid():
                indices_stack.append(index.row())
                index = index.parent()
            indices_stacks.append(indices_stack)
        data.setData("x-napari-bioimage", pickle.dumps(indices_stacks))
        return data

    def dropMimeData(
        self,
        data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:
        if data.hasFormat("x-napari-bioimage") and action in (
            Qt.DropAction.CopyAction,
            Qt.DropAction.MoveAction,
        ):
            indices_stacks = pickle.loads(data.data("x-napari-bioimage").data())
            assert isinstance(indices_stacks, list) and len(indices_stacks) > 0
            for i, indices_stack in enumerate(indices_stacks):
                assert isinstance(indices_stack, list) and len(indices_stack) > 0
                source_images = self._controller.images
                source_row = indices_stack.pop()
                assert isinstance(source_row, int)
                while len(indices_stack) > 0:
                    source_images = source_images[source_row].children
                    source_row = indices_stack.pop()
                    assert isinstance(source_row, int)
                source_image = source_images[source_row]
                if parent.isValid():
                    parent_image = parent.internalPointer()
                    assert isinstance(parent_image, Image)
                    images = parent_image.children
                else:
                    parent_image = None
                    images = self._controller.images
                image = source_image.deepcopy(parent=parent_image)
                if row >= 0 and column >= 0:
                    assert 0 <= row + i <= len(images)
                    assert 0 <= column < len(self.COLUMNS)
                    index = row + i
                else:
                    assert row == -1
                    assert column == -1
                    index = len(images)
                with self.ignore_images_changed():
                    self.beginInsertRows(parent, index, index)
                    images.insert(index, image)
                    self.endInsertRows()
            return True
        return False

    def _on_images_changed(self, event: Event, image: Optional[Image] = None) -> None:
        if self._ignore_images_changed:
            return
        if isinstance(event.sources[0], Image):  # catch EventedModel events
            self._on_image_changed(event, event.sources[0])
            return

        def parent_index():
            if image is not None:
                if image.parent is not None:
                    row = image.parent.children.index(image)
                else:
                    row = self._controller.images.index(image)
                return self.createIndex(row, 0, object=image)
            return QModelIndex()

        # event.sources does not seem to work properly for nested EventedLists
        if image is not None:
            images = image.children
        else:
            images = self._controller.images

        if event.type == "inserting":
            assert isinstance(event.index, int) and 0 <= event.index <= len(images)
            self.beginInsertRows(parent_index(), event.index, event.index)
        elif event.type == "inserted":
            self.endInsertRows()
            assert isinstance(event.value, Image)
            self._connect_image(event.value)
        elif event.type == "removing":
            assert isinstance(event.index, int) and 0 <= event.index < len(images)
            self.beginRemoveRows(parent_index(), event.index, event.index)
        elif event.type == "removed":
            self.endRemoveRows()
            assert isinstance(event.value, Image)
            self._disconnect_image(event.value)
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

    def _connect_image(self, image: Image) -> None:
        assert image._children_callback is None
        image._children_callback = image.children.events.connect(
            lambda e: self._on_images_changed(e, image=image)
        )
        assert image._children_callback is not None
        for child_image in image.children:
            self._connect_image(child_image)

    def _disconnect_image(self, image: Image) -> None:
        for child_image in image.children:
            self._disconnect_image(child_image)
        assert image._children_callback is not None
        image.children.events.disconnect(callback=image._children_callback)
        image._children_callback = None
