from typing import TYPE_CHECKING, Any

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict

if TYPE_CHECKING:
    from ._image import Image


class Layer(EventedModel):
    name: str
    image: "Image"
    metadata: EventedDict[str, Any] = EventedDict()
