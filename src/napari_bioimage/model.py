from typing import Any, Optional, Sequence

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList

#
# The following options were considered:
#
# 1. Custom classes
# - allows for "readonly fields" (properties)
# - dynamic models are possible (e.g. file system)
#
# 2. Inherit from napari.utils.events classes
# - does not allow for "readonly fields" (properties)
# - dynamic models are impossible (may be a good thing)
# - consistent with existing napari models (evented pydantic models)
#
# 3. Inherit from napari.utils.tree classes
# - allows for "readonly fields" (properties)
# - dynamic models are impossible (may be a good thing)
# - re-use existing composite tree pattern implementation
#
# For consistency, option 2 (inherit from napari.utils.events classes) was chosen.
#


class Layer(EventedModel):
    name: str
    image: "Image"  # "readonly field"
    metadata: EventedDict[str, Any] = EventedDict()  # "readonly field"


class Image(EventedModel):
    name: str
    parent: Optional["ImageGroup"] = None  # "readonly field"
    layers: EventedList[Layer] = EventedList(
        basetype=Layer, lookup={str: lambda layer: layer.name}
    )  # "readonly field"

    def collect_layers(self) -> Sequence[Layer]:
        return self.layers


Layer.update_forward_refs(Image=Image)


class ImageGroup(Image):
    children: EventedList[Image] = EventedList(
        basetype=Image, lookup={str: lambda image: image.name}
    )  # "readonly field"

    def collect_layers(self) -> Sequence[Layer]:
        layers = list(super().collect_layers())
        for child in self.children:
            layers += child.collect_layers()
        return layers


Image.update_forward_refs(ImageGroup=ImageGroup)
