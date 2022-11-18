import numpy as np
from napari.components import LayerList
from napari.layers import Image
from napari.utils.events import Event


class ProxyImage(Image):
    def __init__(self, layers: LayerList) -> None:
        super().__init__(np.array([[0, 1]]))
        self._layers = layers
        self._updating = False
        self.events.connect(self._on_event)
        self._connect_events()
        self._update()

    def __del__(self) -> None:
        self._disconnect_events()

    def _connect_events(self) -> None:
        self._layers.selection.events.changed.connect(
            self._on_layers_selection_changed_event
        )

    def _disconnect_events(self) -> None:
        self._layers.selection.events.changed.disconnect(
            self._on_layers_selection_changed_event
        )

    def _on_event(self, event: Event) -> None:
        if hasattr(self, event.type) and not self._updating:
            value = getattr(self, event.type)
            for layer in self._layers.selection:
                if isinstance(layer, Image) and hasattr(layer, event.type):
                    setattr(layer, event.type, value)

    def _on_layers_selection_changed_event(self, event: Event) -> None:
        self._update()

    def _update(self) -> None:
        images = [layer for layer in self._layers.selection if isinstance(layer, Image)]
        if len(images) > 0:
            self._updating = True
            try:
                self.data = np.array(
                    [
                        np.amin([image.contrast_limits_range[0] for image in images]),
                        np.amax([image.contrast_limits_range[1] for image in images]),
                    ]
                )[np.newaxis, :]
                self.reset_contrast_limits()
            finally:
                self._updating = False
