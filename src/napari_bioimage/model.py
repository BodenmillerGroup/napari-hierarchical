from typing import Optional, Sequence

from napari.layers import Layer as NapariLayer
from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList
from pydantic import Field


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Layer(EventedModel):
    name: str
    image: "Image"
    layer: Optional[NapariLayer] = None
    groups: "EventedLayerGroupsDict" = Field(
        default_factory=lambda: EventedLayerGroupsDict()
    )  # grouping --> group

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups._layer = self

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

    # QModelIndex may point to instances that have been garbage-collected by Python
    # Workaround for QImageTreeModel: prevent Python from garbage-collecting objects by
    # retaining a reference indefinitely (but release as much memory as possible)
    def free_memory(self) -> None:
        self.layer = None
        self.groups.clear()


class EventedLayerGroupsDict(EventedDict[str, str]):
    def __init__(self):
        super().__init__(basetype=str)
        self._layer: Optional[Layer] = None

    @property
    def layer(self) -> Layer:
        assert self._layer is not None
        return self._layer


class Image(EventedModel):
    name: str
    parent: Optional["Image"] = None
    children: "EventedImageChildrenList" = Field(
        default_factory=lambda: EventedImageChildrenList()
    )
    layers: "EventedImageLayersList" = Field(
        default_factory=lambda: EventedImageLayersList()
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.children._image = self
        self.layers._image = self

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

    # QModelIndex may point to instances that have been garbage-collected by Python
    # Workaround for QImageTreeModel: prevent Python from garbage-collecting objects by
    # retaining a reference indefinitely (but release as much memory as possible)
    def free_memory(self) -> None:
        for child_image in self.children:
            child_image.free_memory()
        for layer in self.layers:
            layer.free_memory()


class EventedImageChildrenList(EventedList[Image]):
    def __init__(self):
        super().__init__(basetype=Image, lookup={str: lambda image: image.name})
        self._image: Optional[Image] = None

    @property
    def image(self) -> Image:
        assert self._image is not None
        return self._image


class EventedImageLayersList(EventedList[Layer]):
    def __init__(self) -> None:
        super().__init__(basetype=Layer, lookup={str: lambda layer: layer.name})
        self._image: Optional[Image] = None

    @property
    def image(self) -> Image:
        assert self._image is not None
        return self._image


Image.update_forward_refs(
    EventedImageChildrenList=EventedImageChildrenList,
    EventedImageLayersList=EventedImageLayersList,
)

Layer.update_forward_refs(Image=Image, EventedLayerGroupsDict=EventedLayerGroupsDict)
