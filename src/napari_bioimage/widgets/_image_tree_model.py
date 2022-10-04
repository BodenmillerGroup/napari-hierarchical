from typing import Any, Iterable, List, NamedTuple, Optional, Sequence

from napari.utils.events import Event, EventEmitter
from napari.utils.tree import Group as CompositeTreeGroupNode
from napari.utils.tree import Node as CompositeTreeNode
from qtpy.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt

from .._controller import BioImageController
from ..model import Image, ImageGroup

# This tree model implements a composite tree pattern "in parallel"
# This is required to store callback references with each node for deregistration
# (pydantic models are not hashable --> callback references cannot be stored in a dict)


class QImageTreeModel(QAbstractItemModel):
    class Node(CompositeTreeNode):
        def __init__(
            self,
            model: "QImageTreeModel",
            image: Image,
            parent: Optional["QImageTreeModel.GroupNode"] = None,
        ) -> None:
            super().__init__(name=image.name)
            self._init_node(model, image, parent=parent)

        def _init_node(
            self,
            model: "QImageTreeModel",
            image: Image,
            parent: Optional["QImageTreeModel.GroupNode"] = None,
        ) -> None:
            self.parent = parent
            self._model = model
            self._image = image
            self._callbacks: List[EventEmitter] = []
            self._connect_callbacks()

        def __del__(self) -> None:
            self._disconnect_callbacks()

        def _connect_callbacks(
            self,
        ) -> Sequence[EventEmitter]:
            callbacks = [self._image.events.connect(self._model._on_image_changed)]
            self._callbacks += callbacks
            return callbacks

        def _disconnect_callbacks(self) -> None:
            while self._callbacks:
                callback = self._callbacks.pop()
                callback.disconnect()

        @property
        def model(self) -> "QImageTreeModel":
            return self._model

        @property
        def image(self) -> Image:
            return self._image

    class GroupNode(CompositeTreeGroupNode[Node], Node):
        def __init__(
            self,
            model: "QImageTreeModel",
            image_group: ImageGroup,
            parent: Optional["QImageTreeModel.GroupNode"] = None,
        ) -> None:
            CompositeTreeGroupNode.__init__(self, name=image_group.name)
            self._init_node(model, image_group, parent=parent)
            self._image_group = image_group

        @property
        def image_group(self) -> ImageGroup:
            return self._image_group

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
        self._nodes: List[QImageTreeModel.Node] = [
            self._create_node(image) for image in controller.images
        ]
        self._callbacks: List[EventEmitter] = []
        self._connect_callbacks()

    def __del__(self) -> None:
        self._disconnect_callbacks()

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        if 0 <= column < len(self.COLUMNS):
            if parent.isValid():
                parent_group_node = parent.internalPointer()
                assert isinstance(parent_group_node, QImageTreeModel.GroupNode)
                if 0 <= row < len(parent_group_node):
                    node = parent_group_node[row]
                    return self.createIndex(row, column, object=node)
            elif 0 <= row < len(self._nodes):
                node = self._nodes[row]
                return self.createIndex(row, column, object=node)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if index.isValid():
            node = index.internalPointer()
            assert isinstance(node, QImageTreeModel.Node)
            if node.parent is not None:
                if node.parent.parent is not None:
                    row = node.parent.parent.index(node.parent)
                else:
                    row = self._nodes.index(node.parent)
                return self.createIndex(row, 0, object=node.parent)
        return QModelIndex()

    def rowCount(self, index: QModelIndex = QModelIndex()) -> int:
        if index.isValid():
            node = index.internalPointer()
            if isinstance(node, QImageTreeModel.GroupNode):
                return len(node)
            return 0
        return len(self._nodes)

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

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if (
            index.isValid()
            and 0 <= index.column() < len(self.COLUMNS)
            and role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole)
        ):
            node = index.internalPointer()
            assert isinstance(node, QImageTreeModel.Node)
            column = self.COLUMNS[index.column()]
            return getattr(node.image, column.field)
        return None

    def setData(
        self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole
    ) -> bool:
        if (
            index.isValid()
            and 0 <= index.column() < len(self.COLUMNS)
            and role == Qt.ItemDataRole.EditRole
        ):
            node = index.internalPointer()
            assert isinstance(node, QImageTreeModel.Node)
            column = self.COLUMNS[index.column()]
            setattr(node.image, column.field, value)
            return True
        return False

    # def insertRows(
    #     self, row: int, count: int, parent: QModelIndex = QModelIndex()
    # ) -> bool:
    #     return super().insertRows(row, count, parent)

    # def removeRows(
    #     self, row: int, count: int, parent: QModelIndex = QModelIndex()
    # ) -> bool:
    #     return super().removeRows(row, count, parent)

    def _create_node(
        self, image: Image, parent_node: Optional["QImageTreeModel.GroupNode"] = None
    ) -> "QImageTreeModel.Node":
        if isinstance(image, ImageGroup):
            node = QImageTreeModel.GroupNode(self, image, parent=parent_node)
            for child_image in image.children:
                child_node = self._create_node(child_image, parent_node=node)
                node.append(child_node)
            return node
        return QImageTreeModel.Node(self, image, parent=parent_node)

    def _connect_callbacks(self) -> Sequence[EventEmitter]:
        callbacks = [
            self._controller.images.events.inserting.connect(self._on_images_inserting),
            self._controller.images.events.inserted.connect(self._on_images_inserted),
            self._controller.images.events.removing.connect(self._on_images_removing),
            self._controller.images.events.removed.connect(self._on_images_removed),
            self._controller.images.events.moving.connect(self._on_images_moving),
            self._controller.images.events.moved.connect(self._on_images_moved),
            self._controller.images.events.changed.connect(self._on_images_changed),
            self._controller.images.events.reordered.connect(self._on_images_reordered),
        ]
        self._callbacks += callbacks
        return callbacks

    def _disconnect_callbacks(self) -> None:
        while self._callbacks:
            callback = self._callbacks.pop()
            callback.disconnect()

    def _on_images_inserting(self, event: Event) -> None:
        index = event.index
        assert isinstance(index, int)
        self.beginInsertRows(QModelIndex(), index, index)

    def _on_images_inserted(self, event: Event) -> None:
        index = event.index
        image = event.value
        assert isinstance(index, int)
        assert isinstance(image, Image)
        node = self._create_node(image)
        self._nodes.insert(index, node)
        self.endInsertRows()

    def _on_images_removing(self, event: Event) -> None:
        index = event.index
        assert isinstance(index, int)
        self.beginRemoveRows(QModelIndex(), index, index)

    def _on_images_removed(self, event: Event) -> None:
        index = event.index
        assert isinstance(index, int)
        del self._nodes[index]
        self.endRemoveRows()

    def _on_images_moving(self, event: Event) -> None:
        index = event.index
        new_index = event.index
        assert isinstance(index, int)
        assert isinstance(new_index, int)
        self.beginMoveRows(QModelIndex(), index, index, QModelIndex(), new_index)

    def _on_images_moved(self, event: Event) -> None:
        self.endMoveRows()

    def _on_images_changed(self, event: Event) -> None:
        index = event.index
        image = event.value
        assert isinstance(index, int)
        assert isinstance(image, Image)
        del self._nodes[index]
        node = self._create_node(image)
        self._nodes.insert(index, node)
        top_left = self.createIndex(index, 0, object=node)
        bottom_right = self.createIndex(index, len(self.COLUMNS) - 1, object=node)
        self.dataChanged.emit(top_left, bottom_right)

    def _on_images_reordered(self, event: Event) -> None:
        top_left = self.createIndex(0, 0, object=self._nodes[0])
        bottom_right = self.createIndex(
            len(self._nodes) - 1, len(self.COLUMNS) - 1, object=self._nodes[-1]
        )
        self.dataChanged.emit(top_left, bottom_right)

    def _on_image_changed(self, event: Event) -> None:
        column = next(
            (i for i, c in enumerate(self.COLUMNS) if c.field == event.type), None
        )
        if column is not None:
            image = event.source
            assert isinstance(image, Image)
            node = self._search_node_dfs(image)
            assert node is not None
            if node.parent is not None:
                row = node.parent.index(node)
            else:
                row = self._nodes.index(node)
            index = self.createIndex(row, column, object=node)
            self.dataChanged.emit(index, index)

    def _search_node_dfs(
        self, image: Image, current_nodes: Iterable[Node] = None
    ) -> Optional[Node]:
        if current_nodes is None:
            current_nodes = self._nodes
        for current_node in current_nodes:
            if current_node.image == image:
                return current_node
            if isinstance(current_node, QImageTreeModel.GroupNode):
                child_node = self._search_node_dfs(image, current_nodes=current_node)
                if child_node is not None:
                    return child_node
        return None
