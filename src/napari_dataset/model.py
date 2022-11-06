from typing import Generator, List, Optional, Sequence, Tuple

from napari.layers import Layer as NapariLayer
from pydantic import Field

from .utils.parent_aware import (
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

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return self.name

    def get_root(self) -> Tuple["Dataset", Sequence[str]]:
        root_dataset = self
        parent_dataset = root_dataset.get_parent()
        dataset_names: List[str] = []
        while parent_dataset is not None:
            dataset_names.insert(0, root_dataset.name)
            root_dataset = parent_dataset
            parent_dataset = root_dataset.get_parent()
        return root_dataset, dataset_names

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


class Layer(ParentAwareEventedModel[Dataset]):
    name: str
    groups: ParentAwareEventedModelDict["Layer", str, str] = Field(
        default_factory=lambda: ParentAwareEventedModelDict(basetype=str)
    )  # grouping --> group
    napari_layer: Optional[NapariLayer] = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups.set_parent(self)

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return self.name

    def copy(self, *args, **kwargs) -> "Layer":
        layer_copy = super().copy(*args, **kwargs)
        layer_copy.napari_layer = self.napari_layer
        return layer_copy
