from typing import Generator, Optional

from napari.layers import Layer as NapariLayer
from pydantic import Field

from .parent_aware import (
    NestedParentAwareEventedModel,
    NestedParentAwareEventedModelList,
    ParentAwareEventedModel,
    ParentAwareEventedModelDict,
    ParentAwareEventedModelList,
)


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Dataset(NestedParentAwareEventedModel["Dataset"]):
    name: str
    layers: ParentAwareEventedModelList["Dataset", "Layer"] = Field(
        default_factory=lambda: ParentAwareEventedModelList(
            basetype=Layer, lookup={str: lambda layer: layer.name}
        )
    )
    children: NestedParentAwareEventedModelList["Dataset"] = Field(
        default_factory=lambda: NestedParentAwareEventedModelList(
            basetype=Dataset, lookup={str: lambda dataset: dataset.name}
        )
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.layers.set_parent(self)
        self.children.set_parent(self)

    @staticmethod
    def from_dataset(dataset: "Dataset") -> "Dataset":
        new_dataset = Dataset(name=dataset.name)
        new_dataset.layers.extend(Layer.from_layer(layer) for layer in dataset.layers)
        new_dataset.children.extend(
            Dataset.from_dataset(child) for child in dataset.children
        )
        return new_dataset

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return self.name

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

    def show(self) -> None:
        for layer in self.iter_layers(recursive=True):
            layer.show()

    def hide(self) -> None:
        for layer in self.iter_layers(recursive=True):
            layer.hide()

    def unload(self) -> None:
        for layer in self.iter_layers(recursive=True):
            layer.unload()

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
    napari_layer: Optional[NapariLayer] = Field(default=None, exclude=True)
    groups: ParentAwareEventedModelDict["Layer", str, str] = Field(
        default_factory=lambda: ParentAwareEventedModelDict(basetype=str)
    )  # grouping --> group

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups.set_parent(self)

    @staticmethod
    def from_layer(layer: "Layer") -> "Layer":
        new_layer = Layer(name=layer.name, napari_layer=layer.napari_layer)
        new_layer.groups.update(layer.groups)
        return new_layer

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return self.name

    def show(self) -> None:
        assert self.napari_layer is not None
        self.napari_layer.visible = True

    def hide(self) -> None:
        assert self.napari_layer is not None
        self.napari_layer.visible = False

    def unload(self) -> None:
        self.napari_layer = None

    @property
    def loaded(self) -> bool:
        return self.napari_layer is not None

    @property
    def visible(self) -> bool:
        return self.napari_layer is not None and self.napari_layer.visible
