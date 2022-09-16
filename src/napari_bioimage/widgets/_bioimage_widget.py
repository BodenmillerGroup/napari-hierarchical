from napari.viewer import Viewer
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget


class BioImageQWidget(QWidget):
    def __init__(self, napari_viewer: Viewer) -> None:
        super().__init__()
        self.viewer = napari_viewer

        btn = QPushButton("Click me!")
        btn.clicked.connect(self._on_click)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(btn)

    def _on_click(self):
        print("napari has", len(self.viewer.layers), "layers")
