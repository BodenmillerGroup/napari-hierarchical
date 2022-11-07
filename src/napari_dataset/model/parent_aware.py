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

PAT = TypeVar("PAT", bound="ParentAware")


class ParentAware(Generic[PT]):
    def __init__(self) -> None:
        self._parent: Optional[PT] = None

    # do not declare parent as property, to avoid conflicts with EventedModel fields

    def set_parent(self, value: Optional[PT]) -> None:
        self._parent = value

    @property
    def parent(self) -> Optional[PT]:
        return self._parent


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
        if self.parent is not None:
            self.parent._emit_nested_event(source_event)

    def _emit_nested_list_event(self, source_list_event: Event) -> None:
        self._nested_list_event(source_list_event=source_list_event)
        if self.parent is not None:
            self.parent._emit_nested_list_event(source_list_event)

    @property
    def nested_event(self) -> EventEmitter:
        return self._nested_event

    @property
    def nested_list_event(self) -> EventEmitter:
        return self._nested_list_event


class NestedParentAwareEventedModelList(ParentAwareEventedList[NPAEMT, PAT]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.events.connect(self._on_event)

    def _on_event(self, event: Event) -> None:
        if self.parent is not None:
            self.parent._emit_nested_list_event(event)

    def __setitem__(
        self, key: Union[int, slice], value: Union[PAT, Iterable[PAT]]
    ) -> None:
        old_value = self[key]
        if isinstance(key, int):
            assert isinstance(value, ParentAware)
            value.set_parent(self.parent)
        else:
            assert isinstance(value, Iterable)
            for item in value:
                assert isinstance(item, ParentAware)
                item.set_parent(self.parent)
        super().__setitem__(key, value)
        if isinstance(key, int):
            assert isinstance(old_value, ParentAware)
            old_value.set_parent(None)
        else:
            assert isinstance(old_value, Iterable)
            for old_item in old_value:
                assert isinstance(old_item, ParentAware)
                old_item.set_parent(None)

    def __delitem__(self, key: Union[int, slice]) -> None:
        old_value = self[key]
        super().__delitem__(key)
        if isinstance(key, int):
            assert isinstance(old_value, ParentAware)
            old_value.set_parent(None)
        else:
            assert isinstance(old_value, Iterable)
            for old_item in old_value:
                assert isinstance(old_item, ParentAware)
                old_item.set_parent(None)

    def insert(self, index: int, value: PAT) -> None:
        value.set_parent(self.parent)
        super().insert(index, value)

    def set_parent(self, value: Optional[NPAEMT]) -> None:
        super().set_parent(value)
        for item in self:
            item.set_parent(value)
