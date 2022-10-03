from typing import Any, Optional

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList

#
# The following options were considered:
#
# 1. Custom classes
# - dynamic models are possible (e.g. file system)
#
# 2. Inherit from napari.utils.events classes
# - dynamic models are impossible (may be a good thing)
# - consistent with existing napari models (evented pydantic models)
#
# 3. Inherit from napari.utils.tree classes
# - dynamic models are impossible (may be a good thing)
# - re-use existing composite tree pattern implementation
#
# For consistency, option 2 (inherit from napari.utils.events classes) was chosen.
#


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
