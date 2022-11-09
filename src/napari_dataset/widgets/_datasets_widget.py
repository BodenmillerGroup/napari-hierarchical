from typing import Optional, Union

from napari.utils.events import Event
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
from ..model import Dataset
from ._dataset_tree_view import QDatasetTreeView


class QDatasetsWidget(QWidget):
    def __init__(
        self,
        napari_viewer: Viewer,
        parent: Optional[QWidget] = None,
        flags: Union[Qt.WindowFlags, Qt.WindowType] = Qt.WindowFlags(),
    ) -> None:
        super().__init__(parent, flags)
        if controller.viewer != napari_viewer:
            controller.register_viewer(napari_viewer)
        self._dataset_tool_bar = QToolBar("Datasets")
        self._new_dataset_push_button = QPushButton("New")
        self._new_dataset_push_button.clicked.connect(
            self._on_new_dataset_push_button_clicked
        )
        self._delete_dataset_push_button = QPushButton("Delete")
        self._delete_dataset_push_button.clicked.connect(
            self._on_delete_dataset_push_button_clicked
        )
        self._delete_dataset_push_button.setEnabled(
            len(controller.selected_datasets) > 0
        )
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._dataset_tool_bar.addWidget(QLabel("Datasets"))
        self._dataset_tool_bar.addWidget(spacer)
        self._dataset_tool_bar.addWidget(self._new_dataset_push_button)
        self._dataset_tool_bar.addWidget(self._delete_dataset_push_button)
        self._dataset_tree_view = QDatasetTreeView(controller)
        self._init_layout()
        self._connect_events()

    def __del__(self) -> None:
        self._disconnect_events()

    def _init_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self._dataset_tool_bar)
        layout.addWidget(self._dataset_tree_view)
        self.setLayout(layout)

    def _connect_events(self) -> None:
        controller.selected_datasets.events.connect(self._on_selected_datasets_event)

    def _disconnect_events(self) -> None:
        controller.selected_datasets.events.disconnect(self._on_selected_datasets_event)

    def _on_selected_datasets_event(self, event: Event) -> None:
        self._delete_dataset_push_button.setEnabled(
            len(controller.selected_datasets) > 0
        )

    def _on_new_dataset_push_button_clicked(self, checked: bool = False) -> None:
        if len(controller.selected_datasets) == 1:
            datasets = controller.selected_datasets[0].children
        else:
            datasets = controller.datasets
        dataset = Dataset(name="New Dataset")
        datasets.append(dataset)
        controller.selected_datasets.clear()
        controller.selected_datasets.append(dataset)

    def _on_delete_dataset_push_button_clicked(self, checked: bool = False) -> None:
        def get_level(dataset: Dataset, current_level: int = 0) -> int:
            if dataset.parent is not None:
                current_level += 1
                return get_level(dataset.parent, current_level=current_level)
            return current_level

        datasets = sorted(controller.selected_datasets, key=get_level, reverse=True)
        controller.selected_datasets.clear()
        for dataset in datasets:
            if dataset.parent is not None:
                dataset.parent.children.remove(dataset)
            else:
                controller.datasets.remove(dataset)
