from napari.utils.events.containers import SelectableNestableEventedList

from ._image import Image


class Group(Image):
    children: SelectableNestableEventedList[Image] = SelectableNestableEventedList(
        basetype=Image, lookup={str: lambda image: image.name}
    )
