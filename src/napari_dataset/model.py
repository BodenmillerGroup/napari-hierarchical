from typing import Generator, Iterable, List, Optional, Sequence, Tuple

from napari.utils.events import EventedModel
from napari.utils.events.containers import EventedDict, EventedList
from pydantic import Field


class Layer(EventedModel):
    name: str
    groups: "EventedLayerGroupsDict" = Field(
        default_factory=lambda: EventedLayerGroupsDict()
    )  # grouping --> group
    _dataset: Optional["Dataset"] = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.groups._layer = self

    def __hash__(self) -> int:
        return id(self)

    @property
    def dataset(self) -> "Dataset":
        assert self._dataset is not None
        return self._dataset


class EventedLayerGroupsDict(EventedDict[str, str]):
    def __init__(self):
        super().__init__(basetype=str)
        self._layer: Optional[Layer] = None

    @property
    def layer(self) -> Layer:
        assert self._layer is not None
        return self._layer


# do not inherit from napari.utils.tree to avoid conflicts with pydantic-based models
class Dataset(EventedModel):
    name: str
    layers: "EventedDatasetLayersList" = Field(
        default_factory=lambda: EventedDatasetLayersList()
    )
    children: "EventedDatasetChildrenList" = Field(
        default_factory=lambda: EventedDatasetChildrenList()
    )
    _parent: Optional["Dataset"] = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.layers._dataset = self
        for layer in self.layers:
            layer._dataset = self
        self.children._dataset = self
        for child in self.children:
            child._parent = self

    def __hash__(self) -> int:
        return id(self)

    def get_root(self) -> Tuple["Dataset", Sequence[str]]:
        root_dataset = self
        dataset_names: List[str] = []
        while root_dataset._parent is not None:
            dataset_names.insert(0, root_dataset.name)
            root_dataset = root_dataset._parent
        return root_dataset, dataset_names

    def iter_layers(self, recursive: bool = False) -> Generator[Layer, None, None]:
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

    @property
    def parent(self) -> Optional["Dataset"]:
        return self._parent


class EventedDatasetLayersList(EventedList[Layer]):
    def __init__(self):
        super().__init__(basetype=Layer, lookup={str: lambda layer: layer.name})
        self._dataset: Optional[Dataset] = None

    def __setitem__(self, key, value) -> None:
        old_value = self[key]
        if isinstance(value, Layer):
            value._dataset = self._dataset
        elif isinstance(value, Iterable):
            for layer in value:
                assert isinstance(layer, Layer)
                layer._dataset = self._dataset
        super().__setitem__(key, value)
        if isinstance(old_value, Layer):
            old_value._dataset = None
        elif isinstance(old_value, Iterable):
            for old_layer in old_value:
                assert isinstance(old_layer, Layer)
                old_layer._dataset = None

    def __delitem__(self, key) -> None:
        old_value = self[key]
        super().__delitem__(key)
        if isinstance(old_value, Layer):
            old_value._dataset = None
        elif isinstance(old_value, Iterable):
            for old_layer in old_value:
                assert isinstance(old_layer, Layer)
                old_layer._dataset = None

    def insert(self, index: int, value: Layer) -> None:
        value._dataset = self._dataset
        super().insert(index, value)

    @property
    def dataset(self) -> Dataset:
        assert self._dataset is not None
        return self._dataset


class EventedDatasetChildrenList(EventedList[Dataset]):
    def __init__(self):
        super().__init__(basetype=Dataset, lookup={str: lambda dataset: dataset.name})
        self._dataset: Optional[Dataset] = None

    def __setitem__(self, key, value) -> None:
        old_value = self[key]
        if isinstance(value, Dataset):
            value._parent = self._dataset
        elif isinstance(value, Iterable):
            for dataset in value:
                assert isinstance(dataset, Dataset)
                dataset._parent = self._dataset
        super().__setitem__(key, value)
        if isinstance(old_value, Dataset):
            old_value._parent = None
        elif isinstance(old_value, Iterable):
            for old_dataset in old_value:
                assert isinstance(old_dataset, Dataset)
                old_dataset._parent = None

    def __delitem__(self, key) -> None:
        old_value = self[key]
        super().__delitem__(key)
        if isinstance(old_value, Dataset):
            old_value._parent = None
        elif isinstance(old_value, Iterable):
            for old_dataset in old_value:
                assert isinstance(old_dataset, Dataset)
                old_dataset._parent = None

    def insert(self, index: int, value: Dataset) -> None:
        value._parent = self._dataset
        return super().insert(index, value)

    @property
    def dataset(self) -> Dataset:
        assert self._dataset is not None
        return self._dataset


Dataset.update_forward_refs(
    EventedDatasetLayersList=EventedDatasetLayersList,
    EventedDatasetChildrenList=EventedDatasetChildrenList,
)

Layer.update_forward_refs(
    Dataset=Dataset, EventedLayerGroupsDict=EventedLayerGroupsDict
)
