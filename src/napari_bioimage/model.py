from typing import Any, Callable, Optional, Sequence

from napari.layers import Layer as NapariLayer
from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList

# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models


class Layer(EventedModel):
    name: str
    image: "Image"
    layer: Optional[NapariLayer] = None
    metadata: EventedDict[str, Any] = EventedDict()

    def load(self) -> NapariLayer:
        if self.layer is None:
            raise NotImplementedError(f"{self} cannot be loaded")
        return self.layer

    def save(self) -> None:
        raise NotImplementedError(f"{self} cannot be saved")

    @property
    def loaded(self) -> bool:
        return self.layer is not None


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

    # EventedList events are not propagated to "parent" EventedLists
    # Workaround for QImageTreeModel: register a callback for each ImageGroup
    # https://napari.zulipchat.com/#narrow/stream/212875-general/topic/.E2.9C.94.20model.20events.20propagation
    _callback: Optional[Callable] = None

    def collect_layers(self) -> Sequence[Layer]:
        layers = list(super().collect_layers())
        for child in self.children:
            layers += child.collect_layers()
        return layers


Image.update_forward_refs(ImageGroup=ImageGroup)
