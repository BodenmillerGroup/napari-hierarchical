from typing import Any, Optional

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList

# By inheriting from EventedModel, dynamic models deliberately become impossible

# For compatibility with napari.utils.events, do not inherit from napari.utils.tree


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


Layer.update_forward_refs(Image=Image)


class ImageGroup(Image):
    children: EventedList[Image] = EventedList(
        basetype=Image, lookup={str: lambda image: image.name}
    )


Image.update_forward_refs(ImageGroup=ImageGroup)
