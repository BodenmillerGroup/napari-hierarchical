from typing import Any, Optional, Sequence

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList


class Layer(EventedModel):
    name: str
    image: "Image"
    metadata: EventedDict[str, Any] = EventedDict()


class Image(EventedModel):
    name: str
    parent: Optional["ImageGroup"] = None
    layers: EventedList[Layer] = EventedList(
        basetype=Layer, lookup={str: lambda layer: layer.name}
    )

    def collect_layers(self) -> Sequence[Layer]:
        return self.layers


Layer.update_forward_refs(Image=Image)


class ImageGroup(Image):
    children: EventedList[Image] = EventedList(
        basetype=Image, lookup={str: lambda image: image.name}
    )

    def collect_layers(self) -> Sequence[Layer]:
        layers = list(super().collect_layers())
        for child in self.children:
            layers += child.collect_layers()
        return layers


Image.update_forward_refs(ImageGroup=ImageGroup)
