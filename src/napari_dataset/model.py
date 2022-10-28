from typing import Generator, Optional

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList
from pydantic import Field


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Layer(EventedModel):
    name: str
    dataset: "Dataset"
    groups: "EventedLayerGroupsDict" = Field(
        default_factory=lambda: EventedLayerGroupsDict()
    )  # grouping --> group

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups._layer = self


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
    layers: "EventedDatasetLayersList" = Field(
        default_factory=lambda: EventedDatasetLayersList()
    )
    children: "EventedDatasetChildrenList" = Field(
        default_factory=lambda: EventedDatasetChildrenList()
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.children._dataset = self
        self.layers._dataset = self

    def iter_layers(self, recursive: bool = False) -> Generator[Layer, None, None]:
        yield from self.layers
        if recursive:
            for child in self.children:
                yield from child.iter_layers(recursive=recursive)

    def iter_children(
        self, recursive: bool = False
    ) -> Generator["Dataset", None, None]:
        for child in self.children:
            yield child
        if recursive:
            for child in self.children:
                yield from child.iter_children(recursive=recursive)


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
