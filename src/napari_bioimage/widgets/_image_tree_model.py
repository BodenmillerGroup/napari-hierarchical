import pickle
from typing import Any, Callable, Iterable, List, NamedTuple, Optional

from napari.utils.events import Event, EventedList
from qtpy.QtCore import QAbstractItemModel, QMimeData, QModelIndex, QObject, Qt

from .._controller import BioImageController
from ..model import EventedImageChildrenList, Image


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
        self._orphan_images: List[Image] = []
        self._pending_drop_actions: List[Callable[[], None]] = []
        self._remaining_removes_before_drop = 0
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

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
            setattr(image, column.field, value)
            return True
        return False

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
            for i in range(row, row + count):
                image = Image(name="New Image", parent=parent_image)
                images.insert(i, image)
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
            for _ in range(count):
                image = images.pop(row)
                # prevent Python from garbage-collecting objects that are referenced by
                # existing QModelIndex instances, but release as much memory as possible
                self._orphan_images.append(image)
                image.free_memory()
            # finish drag and drop action
            if self._remaining_removes_before_drop > 0:
                self._remaining_removes_before_drop -= count
                if self._remaining_removes_before_drop == 0:
                    while len(self._pending_drop_actions) > 0:
                        drop_action = self._pending_drop_actions.pop(0)
                        drop_action()
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
            if parent.isValid():
                parent_image = parent.internalPointer()
                assert isinstance(parent_image, Image)
                images = parent_image.children
            else:
                parent_image = None
                images = self._controller.images
            if row == -1 and column == -1:
                row = len(images)
            assert 0 <= row <= len(images)
            n = 0
            while len(indices_stacks) > 0:
                indices_stack = indices_stacks.pop(0)
                assert isinstance(indices_stack, list) and len(indices_stack) > 0
                source_images = self._controller.images
                source_row = indices_stack.pop()
                assert isinstance(source_row, int)
                while len(indices_stack) > 0:
                    source_images = source_images[source_row].children
                    source_row = indices_stack.pop()
                    assert isinstance(source_row, int)
                index = row + n
                if images == source_images and index > source_row:
                    index -= 1
                image = source_images[source_row].to_image(parent=parent_image)
                self._pending_drop_actions.append(lambda: images.insert(index, image))
                self._remaining_removes_before_drop += 1
                n += 1
            return True
        return False

    def _connect_events(self) -> None:
        for image in self._controller.images:
            self._connect_image_events(image)
        self._controller.images.events.connect(self._on_images_event)

    def _disconnect_events(self) -> None:
        self._controller.images.events.disconnect(self._on_images_event)
        for image in self._controller.images:
            self._disconnect_image_events(image)

    def _connect_image_events(self, image: Image) -> None:
        for child_image in image.children:
            self._connect_image_events(child_image)
        image.children.events.connect(self._on_images_event)
        image.events.connect(self._on_image_event)

    def _disconnect_image_events(self, image: Image) -> None:
        image.events.disconnect(self._on_image_event)
        image.children.events.disconnect(self._on_images_event)
        for child_image in image.children:
            self._disconnect_image_events(child_image)

    def _on_images_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        assert isinstance(event.source, EventedList)
        if isinstance(event.source, EventedImageChildrenList):
            image = event.source.image
            child_images = image.children
        else:
            image = None
            child_images = self._controller.images

        def get_parent():
            if image is not None:
                if image.parent is not None:
                    parent_row = image.parent.children.index(image)
                else:
                    parent_row = self._controller.images.index(image)
                return self.createIndex(parent_row, 0, object=image)
            return QModelIndex()

        if event.type == "inserting":
            assert isinstance(event.index, int) and 0 <= event.index <= len(
                child_images
            )
            self.beginInsertRows(get_parent(), event.index, event.index)
        elif event.type == "inserted":
            self.endInsertRows()
            assert isinstance(event.value, Image)
            self._connect_image_events(event.value)
        elif event.type == "removing":
            assert isinstance(event.index, int) and 0 <= event.index < len(child_images)
            self._disconnect_image_events(child_images[event.index])
            self.beginRemoveRows(get_parent(), event.index, event.index)
        elif event.type == "removed":
            self.endRemoveRows()
        elif event.type == "moving":
            assert isinstance(event.index, int) and 0 <= event.index < len(child_images)
            assert (
                isinstance(event.new_index, int)
                and 0 <= event.new_index <= len(child_images)
                and event.new_index != event.index
            )
            parent = get_parent()
            self.beginMoveRows(
                parent, event.index, event.index, parent, event.new_index
            )
        elif event.type == "moved":
            self.endMoveRows()
        elif event.type == "changed" and isinstance(event.index, int):
            assert 0 <= event.index < len(child_images)
            left_index = self.createIndex(
                event.index, 0, object=child_images[event.index]
            )
            right_index = self.createIndex(
                event.index, len(self.COLUMNS) - 1, object=child_images[event.index]
            )
            self.dataChanged.emit(left_index, right_index)
        elif event.type in ("changed", "reordered"):
            top_left_index = self.createIndex(0, 0, object=child_images[0])
            bottom_right_index = self.createIndex(
                len(child_images) - 1, len(self.COLUMNS) - 1, object=child_images[-1]
            )
            self.dataChanged.emit(top_left_index, bottom_right_index)

    def _on_image_event(self, event: Event) -> None:
        image = event.source
        assert isinstance(image, Image)
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
