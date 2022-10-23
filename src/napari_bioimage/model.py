from typing import Any, Callable, Optional, Sequence

from napari.layers import Layer as NapariLayer
from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList
from pydantic import Field

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

    def deepcopy(self, image: Optional["Image"] = None) -> "Layer":
        new_layer = Layer(name=self.name, image=image, layer=self.layer)
        new_layer.metadata.update(self.metadata)
        return new_layer

    @property
    def loaded(self) -> bool:
        return self.layer is not None


class Image(EventedModel):
    name: str
    parent: Optional["Image"] = None
    children: EventedList["Image"] = Field(
        default_factory=lambda: EventedList(
            basetype=Image, lookup={str: lambda image: image.name}
        )
    )
    layers: EventedList[Layer] = EventedList(
        basetype=Layer, lookup={str: lambda layer: layer.name}
    )

    # EventedList events are not propagated to "parent" EventedLists
    # Workaround for QImageTreeModel: register a callback for each Image
    # https://napari.zulipchat.com/#narrow/stream/212875-general/topic/.E2.9C.94.20model.20events.20propagation
    _children_callback: Optional[Callable] = None

    def deepcopy(self, parent: Optional["Image"] = None) -> "Image":
        new_image = Image(name=self.name, parent=parent)
        for child_image in self.children:
            new_child_image = child_image.deepcopy(parent=new_image)
            new_image.children.append(new_child_image)
        for layer in self.layers:
            new_layer = layer.deepcopy(image=new_image)
            new_image.layers.append(new_layer)
        return new_image

    def collect_layers(self) -> Sequence[Layer]:
        layers = list(self.layers)
        for child_image in self.children:
            layers += child_image.collect_layers()
        return layers


Layer.update_forward_refs(Image=Image)
