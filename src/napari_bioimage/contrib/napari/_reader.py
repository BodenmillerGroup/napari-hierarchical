import os
from pathlib import Path
from typing import Union

from napari_bioimage import controller
from napari_bioimage.model import Image, Layer

PathLike = Union[str, os.PathLike]


def read_napari(path: PathLike) -> Image:
    assert controller.viewer is not None
    image = Image(name=Path(path).name)
    napari_layers = controller.viewer.open(path, plugin=None)  # TODO fix infinite loop
    for napari_layer in napari_layers:
        controller.viewer.layers.remove(napari_layer)
        layer = Layer(
            name=f"{image.name} [{napari_layer.name}]", image=image, layer=napari_layer
        )
        image.layers.append(layer)
    return image
