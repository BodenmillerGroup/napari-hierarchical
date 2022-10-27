from typing import Optional, Sequence

from napari.layers import Layer as NapariLayer
from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList
from pydantic import Field


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Layer(EventedModel):
    name: str
    dataset: "Dataset"
    layer: Optional[NapariLayer] = None
    groups: "EventedLayerGroupsDict" = Field(
        default_factory=lambda: EventedLayerGroupsDict()
    )  # grouping --> group

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups._layer = self

    def load(self) -> NapariLayer:
        if self.layer is None:
            raise NotImplementedError(f"{self} cannot be loaded")
        return self.layer

    def save(self) -> None:
        raise NotImplementedError(f"{self} cannot be saved")

    def to_layer(self, dataset: Optional["Dataset"] = None) -> "Layer":
        new_layer = Layer(name=self.name, dataset=dataset, layer=self.layer)
        new_layer.groups.update(self.groups)
        return new_layer

    @property
    def loaded(self) -> bool:
        return self.layer is not None

    # QModelIndex may point to instances that have been garbage-collected by Python
    # Workaround for QDatasetTreeModel: prevent Python from garbage-collecting objects
    # by retaining a reference indefinitely (but release as much memory as possible)
    def free_memory(self) -> None:
        self.layer = None
        self.groups.clear()


class EventedLayerGroupsDict(EventedDict[str, str]):
    def __init__(self):
        super().__init__(basetype=str)
        self._layer: Optional[Layer] = None

    @property
    def layer(self) -> Layer:
        assert self._layer is not None
        return self._layer


class Dataset(EventedModel):
    name: str
    parent: Optional["Dataset"] = None
    children: "EventedDatasetChildrenList" = Field(
        default_factory=lambda: EventedDatasetChildrenList()
    )
    layers: "EventedDatasetLayersList" = Field(
        default_factory=lambda: EventedDatasetLayersList()
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.children._dataset = self
        self.layers._dataset = self

    def to_dataset(self, parent: Optional["Dataset"] = None) -> "Dataset":
        new_dataset = Dataset(name=self.name, parent=parent)
        for child_dataset in self.children:
            new_child_dataset = child_dataset.to_dataset(parent=new_dataset)
            new_dataset.children.append(new_child_dataset)
        for layer in self.layers:
            new_layer = layer.to_layer(dataset=new_dataset)
            new_dataset.layers.append(new_layer)
        return new_dataset

    def get_layers(self, recursive: bool = False) -> Sequence[Layer]:
        layers = list(self.layers)
        if recursive:
            for child_dataset in self.children:
                layers += child_dataset.get_layers(recursive=True)
        return layers

    # QModelIndex may point to instances that have been garbage-collected by Python
    # Workaround for QDatasetTreeModel: prevent Python from garbage-collecting objects
    # by retaining a reference indefinitely (but release as much memory as possible)
    def free_memory(self) -> None:
        for child_dataset in self.children:
            child_dataset.free_memory()
        for layer in self.layers:
            layer.free_memory()


class EventedDatasetChildrenList(EventedList[Dataset]):
    def __init__(self):
        super().__init__(basetype=Dataset, lookup={str: lambda dataset: dataset.name})
        self._dataset: Optional[Dataset] = None

    @property
    def dataset(self) -> Dataset:
        assert self._dataset is not None
        return self._dataset


class EventedDatasetLayersList(EventedList[Layer]):
    def __init__(self) -> None:
        super().__init__(basetype=Layer, lookup={str: lambda layer: layer.name})
        self._dataset: Optional[Dataset] = None

    @property
    def dataset(self) -> Dataset:
        assert self._dataset is not None
        return self._dataset


Dataset.update_forward_refs(
    EventedDatasetChildrenList=EventedDatasetChildrenList,
    EventedDatasetLayersList=EventedDatasetLayersList,
)

Layer.update_forward_refs(
    Dataset=Dataset, EventedLayerGroupsDict=EventedLayerGroupsDict
)
