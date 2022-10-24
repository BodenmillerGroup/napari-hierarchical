from typing import Callable, Optional, Sequence

from napari.layers import Layer as NapariLayer
from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList
from pydantic import Field


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Layer(EventedModel):
    name: str
    image: "Image"
    layer: Optional[NapariLayer] = None
    groups: EventedDict[str, str] = EventedDict()  # grouping --> group

    def load(self) -> NapariLayer:
        if self.layer is None:
            raise NotImplementedError(f"{self} cannot be loaded")
        return self.layer

    def save(self) -> None:
        raise NotImplementedError(f"{self} cannot be saved")

    def to_layer(self, image: Optional["Image"] = None) -> "Layer":
        new_layer = Layer(name=self.name, image=image, layer=self.layer)
        new_layer.groups.update(self.groups)
        return new_layer

    @property
    def loaded(self) -> bool:
        return self.layer is not None

    # Workaround for QLayerGroupsWidget
    _groups_callback: Optional[Callable] = None

    # QModelIndex may point to instances that have been garbage-collected by Python
    # Workaround for QImageTreeModel: prevent Python from garbage-collecting objects by
    # retaining a reference indefinitely (but release as much memory as possible)
    def free_memory(self) -> None:
        self.layer = None
        self.groups.clear()


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

    def to_image(self, parent: Optional["Image"] = None) -> "Image":
        new_image = Image(name=self.name, parent=parent)
        for child_image in self.children:
            new_child_image = child_image.to_image(parent=new_image)
            new_image.children.append(new_child_image)
        for layer in self.layers:
            new_layer = layer.to_layer(image=new_image)
            new_image.layers.append(new_layer)
        return new_image

    def get_layers(self, recursive: bool = False) -> Sequence[Layer]:
        layers = list(self.layers)
        if recursive:
            for child_image in self.children:
                layers += child_image.get_layers(recursive=True)
        return layers

    # EventedList events are not propagated to "parent" EventedLists
    # Workaround for QImageTreeModel: register a callback for each Image
    # https://napari.zulipchat.com/#narrow/stream/212875-general/topic/.E2.9C.94.20model.20events.20propagation
    _children_callback: Optional[Callable] = None

    # QModelIndex may point to instances that have been garbage-collected by Python
    # Workaround for QImageTreeModel: prevent Python from garbage-collecting objects by
    # retaining a reference indefinitely (but release as much memory as possible)
    def free_memory(self) -> None:
        for child_image in self.children:
            child_image.free_memory()
        for layer in self.layers:
            layer.free_memory()


Layer.update_forward_refs(Image=Image)
