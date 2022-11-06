from typing import Generic, Iterable, Optional, TypeVar, Union

from napari.utils.events import (
    Event,
    EventedDict,
    EventedList,
    EventedModel,
    EventEmitter,
)

PT = TypeVar("PT")
T = TypeVar("T")
KT = TypeVar("KT")
VT = TypeVar("VT")


class ParentAware(Generic[PT]):
    def __init__(self) -> None:
        self._parent: Optional[PT] = None

    # do not declare parent as property, to avoid conflicts with EventedModel fields

    def get_parent(self) -> Optional[PT]:
        return self._parent

    def set_parent(self, value: Optional[PT]) -> None:
        self._parent = value


class ParentAwareEventedList(ParentAware[PT], EventedList[T]):
    def __init__(self, *args, **kwargs) -> None:
        EventedList.__init__(self, *args, **kwargs)
        ParentAware.__init__(self)


class ParentAwareEventedDict(ParentAware[PT], EventedDict[KT, VT]):
    def __init__(self, *args, **kwargs) -> None:
        EventedDict.__init__(self, *args, **kwargs)
        ParentAware.__init__(self)


PAEMT = TypeVar("PAEMT", bound="ParentAwareEventedModel")


class ParentAwareEventedModel(ParentAware[PT], EventedModel):
    _parent: Optional[PT] = None

    def __init__(self, **kwargs):
        EventedModel.__init__(self, **kwargs)
        ParentAware.__init__(self)


class ParentAwareEventedModelList(ParentAwareEventedList[PAEMT, T]):
    pass


class ParentAwareEventedModelDict(ParentAwareEventedDict[PAEMT, KT, VT]):
    pass


NPAEMT = TypeVar("NPAEMT", bound="NestedParentAwareEventedModel")


class NestedParentAwareEventedModel(ParentAwareEventedModel[NPAEMT]):
    _nested_event: EventEmitter = EventEmitter(type="nested")
    _nested_list_event: EventEmitter = EventEmitter(type="nested_list")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._nested_event.source = self
        self._nested_list_event.source = self
        self.events.connect(self._emit_nested_event)

    def _emit_nested_event(self, source_event: Event) -> None:
        self._nested_event(source_event=source_event)
        parent = self.get_parent()
        if parent is not None:
            parent._emit_nested_event(source_event)

    def _emit_nested_list_event(self, source_event: Event) -> None:
        self._nested_list_event(source_event=source_event)
        parent = self.get_parent()
        if parent is not None:
            parent._emit_nested_list_event(source_event)

    @property
    def nested_event(self) -> EventEmitter:
        return self._nested_event

    @property
    def nested_list_event(self) -> EventEmitter:
        return self._nested_list_event


class NestedParentAwareEventedModelList(ParentAwareEventedModelList[NPAEMT, NPAEMT]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.events.connect(self._emit_parent_nested_list_event)

    def _emit_parent_nested_list_event(self, source_event: Event) -> None:
        parent = self.get_parent()
        if parent is not None:
            parent._emit_nested_list_event(source_event)

    def __setitem__(
        self, key: Union[int, slice], value: Union[NPAEMT, Iterable[NPAEMT]]
    ) -> None:
        old_value = self[key]
        parent = self.get_parent()
        if isinstance(value, ParentAwareEventedModel):
            value.set_parent(parent)
        else:
            for item in value:
                item.set_parent(parent)
        super().__setitem__(key, value)
        if isinstance(old_value, ParentAwareEventedModel):
            old_value.set_parent(None)
        else:
            for old_item in old_value:
                old_item.set_parent(None)

    def __delitem__(self, key: Union[int, slice]) -> None:
        old_value = self[key]
        super().__delitem__(key)
        if isinstance(old_value, ParentAwareEventedModel):
            old_value.set_parent(None)
        else:
            for old_item in old_value:
                old_item.set_parent(None)

    def insert(self, index: int, value: NPAEMT) -> None:
        parent = self.get_parent()
        value.set_parent(parent)
        super().insert(index, value)

    def set_parent(self, value: Optional[NPAEMT]) -> None:
        super().set_parent(value)
        for item in self:
            item.set_parent(value)
