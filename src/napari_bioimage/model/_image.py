from typing import TYPE_CHECKING, Optional

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedList

from ._layer import Layer

if TYPE_CHECKING:
    from ._group import Group


class Image(EventedModel):
    name: str
    parent: Optional["Group"] = None
    layers: EventedList[Layer] = EventedList(
        basetype=Layer, lookup={str: lambda layer: layer.name}
    )
