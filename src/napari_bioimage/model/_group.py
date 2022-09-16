from typing import List, Optional, Sequence


class Group:
    def __init__(self, name: str, parent: Optional["Group"] = None) -> None:
        self._name = name
        self._parent = parent
        self._children: List[Group] = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def parent(self) -> Optional["Group"]:
        return self._parent

    @parent.setter
    def parent(self, value: Optional["Group"]) -> None:
        self._parent = value

    @property
    def children(self) -> Sequence["Group"]:
        return self._children

    def append_child(self, child: "Group") -> None:
        self.insert_child(len(self._children), child)

    def insert_child(self, index: int, child: "Group") -> None:
        self._children.insert(index, child)

    def remove_child(self, child: "Group") -> None:
        self._children.remove(child)
