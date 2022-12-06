from typing import Generic, Iterable, Optional, TypeVar, Union

from napari.utils.events import (
    Event,
    EventedDict,
    EventedList,
    EventedModel,
    EventEmitter,
)

_PT = TypeVar("_PT")
_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")

_PAT = TypeVar("_PAT", bound="ParentAware")


class ParentAware(Generic[_PT]):
    def __init__(self) -> None:
        self._parent: Optional[_PT] = None

    # do not declare parent as property, to avoid conflicts with EventedModel fields

    def set_parent(self, value: Optional[_PT]) -> None:
        self._parent = value

    @property
    def parent(self) -> Optional[_PT]:
        return self._parent


class ParentAwareEventedList(ParentAware[_PT], EventedList[_T]):
    def __init__(self, *args, **kwargs) -> None:
        EventedList.__init__(self, *args, **kwargs)
        ParentAware.__init__(self)


class ParentAwareEventedDict(ParentAware[_PT], EventedDict[_KT, _VT]):
    def __init__(self, *args, **kwargs) -> None:
        EventedDict.__init__(self, *args, **kwargs)
        ParentAware.__init__(self)


_PAEMT = TypeVar("_PAEMT", bound="ParentAwareEventedModel")


class ParentAwareEventedModel(ParentAware[_PT], EventedModel):
    _parent: Optional[_PT] = None

    def __init__(self, **kwargs):
        EventedModel.__init__(self, **kwargs)
        ParentAware.__init__(self)


_NPAEMT = TypeVar("_NPAEMT", bound="NestedParentAwareEventedModel")


class NestedParentAwareEventedModel(ParentAwareEventedModel[_NPAEMT]):
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


class NestedParentAwareEventedModelList(ParentAwareEventedList[_NPAEMT, _PAT]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.events.connect(self._on_event)
        self.dirty = False

    def _on_event(self, event: Event) -> None:
        if self.parent is not None:
            self.parent._emit_nested_list_event(event)

    def insert(self, index: int, value: _PAT) -> None:
        value.set_parent(self.parent)
        super().insert(index, value)
        self.dirty = True

    def __getitem__(self, key):
        if isinstance(key, slice):
            raise NotImplementedError("slicing is not supported")
        result = super().__getitem__(key)
        assert not isinstance(result, NestedParentAwareEventedModelList)
        return result

    def __setitem__(
        self, key: Union[int, slice], value: Union[_PAT, Iterable[_PAT]]
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
        self.dirty = True

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
        self.dirty = True

    def set_parent(self, value: Optional[_NPAEMT]) -> None:
        super().set_parent(value)
        for item in self:
            item.set_parent(value)

    def commit(self) -> None:
        self.dirty = False
