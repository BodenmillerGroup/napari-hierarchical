from typing import Any, Generator, Optional

from napari.layers import Layer
from napari.utils.events import Event
from pydantic import Field

from .utils.parent_aware import (
    NestedParentAwareEventedModel,
    NestedParentAwareEventedModelList,
    ParentAwareEventedDict,
    ParentAwareEventedModel,
)


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Group(NestedParentAwareEventedModel["Group"]):
    class ArrayList(NestedParentAwareEventedModelList["Group", "Array"]):
        def __init__(self) -> None:
            super().__init__(basetype=Array, lookup={str: lambda array: array.name})

    class GroupList(NestedParentAwareEventedModelList["Group", "Group"]):
        def __init__(self) -> None:
            super().__init__(basetype=Group, lookup={str: lambda group: group.name})

    name: str
    arrays: ArrayList = Field(default_factory=ArrayList, allow_mutation=False)
    children: GroupList = Field(default_factory=GroupList, allow_mutation=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.arrays.set_parent(self)
        self.children.set_parent(self)
        self.events.add(loaded=Event, visible=Event)

    @staticmethod
    def from_group(group: "Group") -> "Group":
        new_group = Group(name=group.name)
        new_group.arrays.extend(Array.from_array(array) for array in group.arrays)
        new_group.children.extend(Group.from_group(child) for child in group.children)
        return new_group

    def show(self) -> None:
        for array in self.iter_arrays(recursive=True):
            if array.loaded and not array.visible:
                array.show()

    def hide(self) -> None:
        for array in self.iter_arrays(recursive=True):
            if array.loaded and array.visible:
                array.hide()

    def commit(self) -> None:
        self.arrays.commit()
        self.children.commit()
        for child in self.children:
            child.commit()

    def iter_arrays(self, recursive: bool = False) -> Generator["Array", None, None]:
        yield from self.arrays
        if recursive:
            for child in self.children:
                yield from child.iter_arrays(recursive=recursive)

    def iter_children(self, recursive: bool = False) -> Generator["Group", None, None]:
        yield from self.children
        if recursive:
            for child in self.children:
                yield from child.iter_children(recursive=recursive)

    def __hash__(self) -> int:
        return object.__hash__(self)

    def __eq__(self, other) -> bool:
        return object.__eq__(self, other)

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return repr(self)

    def _emit_loaded_event(self, source_array_event: Event) -> None:
        self.events.loaded(value=self.loaded, source_array_event=source_array_event)
        if self.parent is not None:
            self.parent._emit_loaded_event(source_array_event)

    def _emit_visible_event(self, source_array_event: Event) -> None:
        self.events.visible(value=self.visible, source_array_event=source_array_event)
        if self.parent is not None:
            self.parent._emit_visible_event(source_array_event)

    @property
    def loaded(self) -> Optional[bool]:
        # evaluate any before all to catch empty iterables!
        if not any(array.loaded for array in self.iter_arrays(recursive=True)):
            return False
        if all(array.loaded for array in self.iter_arrays(recursive=True)):
            return True
        return None

    @property
    def visible(self) -> Optional[bool]:
        # evaluate any before all to catch empty iterables!
        if not any(
            array.visible for array in self.iter_arrays(recursive=True) if array.loaded
        ):
            return False
        if all(
            array.visible for array in self.iter_arrays(recursive=True) if array.loaded
        ):
            return True
        return None

    @property
    def dirty(self) -> bool:
        return (
            self.arrays.dirty
            or self.children.dirty
            or any(child.dirty for child in self.children)
        )


class Array(ParentAwareEventedModel[Group]):
    # avoid parameterized generics in type annotations for pydantic
    class FlatGroupingGroupsDict(ParentAwareEventedDict["Array", str, str]):
        def __init__(self) -> None:
            super().__init__(basetype=str)

    name: str
    layer: Optional[Layer] = None
    flat_grouping_groups: FlatGroupingGroupsDict = Field(
        default_factory=FlatGroupingGroupsDict, allow_mutation=False
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.flat_grouping_groups.set_parent(self)
        self.events.add(loaded=Event, visible=Event)
        self.events.name.connect(self._on_name_event)
        self.events.layer.connect(self._on_layer_event)
        self.events.loaded.connect(self._on_loaded_event)
        self.events.visible.connect(self._on_visible_event)
        layer = kwargs.get("layer")
        if layer is not None:
            layer.events.name.connect(self._on_layer_name_event)
            layer.events.visible.connect(self._on_layer_visible_event)

    @staticmethod
    def from_array(array: "Array") -> "Array":
        new_array = Array(name=array.name, layer=array.layer)
        new_array.flat_grouping_groups.update(array.flat_grouping_groups)
        return new_array

    def show(self) -> None:
        assert self.layer is not None
        self.layer.visible = True

    def hide(self) -> None:
        assert self.layer is not None
        self.layer.visible = False

    def __hash__(self) -> int:
        return object.__hash__(self)

    def __eq__(self, other) -> bool:
        return object.__eq__(self, other)

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return repr(self)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "layer" and self.layer is not None:
            self.layer.events.name.disconnect(self._on_layer_name_event)
            self.layer.events.visible.disconnect(self._on_layer_visible_event)
        super().__setattr__(name, value)
        if name == "layer" and self.layer is not None:
            self.layer.events.name.connect(self._on_layer_name_event)
            self.layer.events.visible.connect(self._on_layer_visible_event)

    def _on_name_event(self, event: Event) -> None:
        if self.layer is not None:
            self.layer.name = self.name

    def _on_layer_event(self, event: Event) -> None:
        if self.layer is not None:
            self.name = self.layer.name
        self._emit_loaded_event(event)
        self._emit_visible_event(event)

    def _on_layer_name_event(self, event: Event) -> None:
        assert self.layer is not None
        self.name = self.layer.name

    def _on_layer_visible_event(self, event: Event) -> None:
        assert self.layer is not None
        self._emit_visible_event(event)

    def _on_loaded_event(self, event: Event) -> None:
        if self.parent is not None:
            self.parent._emit_loaded_event(event)

    def _on_visible_event(self, event: Event) -> None:
        if self.parent is not None:
            self.parent._emit_visible_event(event)

    def _emit_loaded_event(self, source_event: Event) -> None:
        self.events.loaded(value=self.loaded, source_event=source_event)

    def _emit_visible_event(self, source_event: Event) -> None:
        self.events.visible(value=self.visible, source_event=source_event)

    @property
    def loaded(self) -> bool:
        return self.layer is not None

    @property
    def visible(self) -> bool:
        return self.layer is not None and self.layer.visible
