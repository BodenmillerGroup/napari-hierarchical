from typing import Any, Generator, Optional

from napari.layers import Layer as NapariLayer
from napari.utils.events import Event
from pydantic import Field

from .parent_aware import (
    NestedParentAwareEventedModel,
    NestedParentAwareEventedModelList,
    ParentAwareEventedDict,
    ParentAwareEventedModel,
)


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Dataset(NestedParentAwareEventedModel["Dataset"]):
    name: str
    layers: NestedParentAwareEventedModelList["Dataset", "Layer"] = Field(
        default_factory=lambda: NestedParentAwareEventedModelList(
            basetype=Layer, lookup={str: lambda layer: layer.name}
        )
    )
    children: NestedParentAwareEventedModelList["Dataset", "Dataset"] = Field(
        default_factory=lambda: NestedParentAwareEventedModelList(
            basetype=Dataset, lookup={str: lambda dataset: dataset.name}
        )
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.layers.set_parent(self)
        self.children.set_parent(self)
        self.events.add(loaded=Event, visible=Event)

    @staticmethod
    def from_dataset(dataset: "Dataset") -> "Dataset":
        new_dataset = Dataset(name=dataset.name)
        new_dataset.layers.extend(Layer.from_layer(layer) for layer in dataset.layers)
        new_dataset.children.extend(
            Dataset.from_dataset(child) for child in dataset.children
        )
        return new_dataset

    def show(self) -> None:
        for layer in self.iter_layers(recursive=True):
            layer.show()

    def hide(self) -> None:
        for layer in self.iter_layers(recursive=True):
            layer.hide()

    def iter_layers(self, recursive: bool = False) -> Generator["Layer", None, None]:
        yield from self.layers
        if recursive:
            for child in self.children:
                yield from child.iter_layers(recursive=recursive)

    def iter_children(
        self, recursive: bool = False
    ) -> Generator["Dataset", None, None]:
        yield from self.children
        if recursive:
            for child in self.children:
                yield from child.iter_children(recursive=recursive)

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return self.name

    def _emit_loaded_event(self, source_layer_event: Event) -> None:
        self.events.loaded(value=self.loaded, source_layer_event=source_layer_event)
        if self.parent is not None:
            self.parent._emit_loaded_event(source_layer_event)

    def _emit_visible_event(self, source_layer_event: Event) -> None:
        self.events.visible(value=self.visible, source_layer_event=source_layer_event)
        if self.parent is not None:
            self.parent._emit_visible_event(source_layer_event)

    @property
    def loaded(self) -> Optional[bool]:
        n = 0
        n_loaded = 0
        for layer in self.iter_layers(recursive=True):
            n += 1
            if layer.loaded:
                n_loaded += 1
        if n_loaded == 0:
            return False
        if n_loaded == n:
            return True
        return None

    @property
    def visible(self) -> Optional[bool]:
        n = 0
        n_visible = 0
        for layer in self.iter_layers(recursive=True):
            n += 1
            if layer.visible:
                n_visible += 1
        if n_visible == 0:
            return False
        if n_visible == n:
            return True
        return None


class Layer(ParentAwareEventedModel[Dataset]):
    name: str
    napari_layer: Optional[NapariLayer] = None
    loaded_napari_layer: Optional[NapariLayer] = Field(
        default=None, allow_mutation=False
    )
    groups: ParentAwareEventedDict["Layer", str, str] = Field(
        default_factory=lambda: ParentAwareEventedDict(basetype=str)
    )  # grouping --> group

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups.set_parent(self)
        self.events.add(loaded=Event, visible=Event)
        self.events.name.connect(self._on_name_event)
        self.events.napari_layer.connect(self._on_napari_layer_event)
        self.events.loaded.connect(self._on_loaded_event)
        self.events.visible.connect(self._on_visible_event)

    @staticmethod
    def from_layer(layer: "Layer") -> "Layer":
        new_layer = Layer(
            name=layer.name,
            napari_layer=layer.napari_layer,
            loaded_napari_layer=layer.loaded_napari_layer,
        )
        new_layer.groups.update(layer.groups)
        return new_layer

    def show(self) -> None:
        assert self.napari_layer is not None
        self.napari_layer.visible = True

    def hide(self) -> None:
        assert self.napari_layer is not None
        self.napari_layer.visible = False

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return self.name

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "napari_layer" and self.napari_layer is not None:
            self.napari_layer.events.name.disconnect(self._on_napari_layer_name_event)
            self.napari_layer.events.visible.disconnect(
                self._on_napari_layer_visible_event
            )
            del self.napari_layer.metadata["napari-dataset-layer"]
        super().__setattr__(name, value)
        if name == "napari_layer" and self.napari_layer is not None:
            self.napari_layer.metadata["napari-dataset-layer"] = self
            self.napari_layer.events.name.connect(self._on_napari_layer_name_event)
            self.napari_layer.events.visible.connect(
                self._on_napari_layer_visible_event
            )

    def _on_name_event(self, event: Event) -> None:
        if self.napari_layer is not None:
            self.napari_layer.name = self.name

    def _on_napari_layer_event(self, event: Event) -> None:
        if self.napari_layer is not None:
            self.name = self.napari_layer.name
        self._emit_loaded_event(event)
        self._emit_visible_event(event)

    def _on_napari_layer_name_event(self, event: Event) -> None:
        assert self.napari_layer is not None
        self.name = self.napari_layer.name

    def _on_napari_layer_visible_event(self, event: Event) -> None:
        assert self.napari_layer is not None
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
        return self.napari_layer is not None

    @property
    def visible(self) -> bool:
        return self.napari_layer is not None and self.napari_layer.visible
