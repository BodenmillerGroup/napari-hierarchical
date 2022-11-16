import os
from typing import List, Optional, Set, Union

from napari.layers import Layer
from napari.utils.events import Event, EventedList, SelectableEventedList
from napari.viewer import Viewer
from pluggy import PluginManager

from . import hookspecs
from .model import Array, Group
from .utils.parent_aware import ParentAware

PathLike = Union[str, os.PathLike]


class HierarchicalController:
    def __init__(self) -> None:
        self._pm = PluginManager("napari-hierarchical")
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints("napari-hierarchical")
        self._viewer: Optional[Viewer] = None
        self._groups: EventedList[Group] = EventedList(
            basetype=Group, lookup={str: lambda group: group.name}
        )
        self._selected_groups: EventedList[Group] = EventedList(
            basetype=Group, lookup={str: lambda group: group.name}
        )
        self._current_arrays: SelectableEventedList[Array] = SelectableEventedList(
            basetype=Array, lookup={str: lambda array: array.name}
        )
        self._updating_layers_selection = False
        self._updating_current_arrays_selection = False
        self._groups.events.connect(self._on_groups_event)
        self._selected_groups.events.connect(self._on_selected_groups_event)
        self._current_arrays.selection.events.changed.connect(
            self._on_current_arrays_selection_changed_event
        )

    def __del__(self) -> None:
        if self._viewer is not None:
            self._viewer.layers.events.disconnect(self._on_layers_event)
            self._viewer.layers.selection.events.changed.disconnect(
                self._on_layers_selection_changed_event
            )

    def register_viewer(self, viewer: Viewer) -> None:
        assert self._viewer is None
        self._viewer = viewer
        viewer.layers.events.connect(self._on_layers_event)
        viewer.layers.selection.events.changed.connect(
            self._on_layers_selection_changed_event
        )

    def can_read_group(self, path: PathLike) -> bool:
        return self._get_group_reader_function(path) is not None

    def can_write_group(self, path: PathLike, group: Group) -> bool:
        return self._get_group_writer_function(path, group) is not None

    def can_load_group(self, group: Group) -> bool:
        return all(
            self.can_load_array(array) for array in group.iter_arrays(recursive=True)
        )

    def can_save_group(self, group: Group) -> bool:
        return all(
            self.can_save_array(array) for array in group.iter_arrays(recursive=True)
        )

    def can_load_array(self, array: Array) -> bool:
        return (
            array.loaded_layer is not None
            or self._get_array_loader_function(array) is not None
        )

    def can_save_array(self, array: Array) -> bool:
        return self._get_array_saver_function(array) is not None

    def read_group(self, path: PathLike) -> Group:
        group_reader_function = self._get_group_reader_function(path)
        if group_reader_function is None:
            raise HierarchicalControllerException(f"No group reader found for {path}")
        try:
            group = group_reader_function(path)
        except Exception as e:
            raise HierarchicalControllerException(e)
        self._groups.append(group)
        return group

    def write_group(self, path: PathLike, group: Group) -> None:
        group_writer_function = self._get_group_writer_function(path, group)
        if group_writer_function is None:
            raise HierarchicalControllerException(f"No group writer found for {path}")
        try:
            group_writer_function(path, group)
        except Exception as e:
            raise HierarchicalControllerException(e)

    def load_group(self, group: Group) -> None:
        for array in group.iter_arrays(recursive=True):
            self.load_array(array)

    def save_group(self, group: Group) -> None:
        for array in group.iter_arrays(recursive=True):
            self.save_array(array)

    def unload_group(self, group: Group) -> None:
        for array in group.iter_arrays(recursive=True):
            self.unload_array(array)

    def load_array(self, array: Array) -> None:
        assert self._viewer is not None
        if not array.loaded:
            if array.loaded_layer is not None:
                array.layer = array.loaded_layer
            else:
                array_loader_function = self._get_array_loader_function(array)
                if array_loader_function is None:
                    raise HierarchicalControllerException(
                        f"No array loader found for {array}"
                    )
                try:
                    array_loader_function(array)
                except Exception as e:
                    raise HierarchicalControllerException(e)
            assert array.layer is not None
            self._viewer.add_layer(array.layer)

    def save_array(self, array: Array) -> None:
        if array.layer is None:
            raise HierarchicalControllerException(f"Array is not loaded: {array}")
        array_saver_function = self._get_array_saver_function(array)
        if array_saver_function is None:
            raise HierarchicalControllerException(f"No array saver found for {array}")
        try:
            array_saver_function(array)
        except Exception as e:
            raise HierarchicalControllerException(e)

    def unload_array(self, array: Array) -> None:
        if array.layer is not None:
            if self._viewer is not None and array.layer in self._viewer.layers:
                self._viewer.layers.remove(array.layer)
            array.layer = None

    def _get_group_reader_function(
        self, path: PathLike
    ) -> Optional[hookspecs.GroupReaderFunction]:
        return self._pm.hook.napari_hierarchical_get_group_reader(path=path)

    def _get_group_writer_function(
        self, path: PathLike, group: Group
    ) -> Optional[hookspecs.GroupWriterFunction]:
        return self._pm.hook.napari_hierarchical_get_group_writer(
            path=path, group=group
        )

    def _get_array_loader_function(
        self, array: Array
    ) -> Optional[hookspecs.ArrayLoaderFunction]:
        return self._pm.hook.napari_hierarchical_get_array_loader(array=array)

    def _get_array_saver_function(
        self, array: Array
    ) -> Optional[hookspecs.ArraySaverFunction]:
        return self._pm.hook.napari_hierarchical_get_array_saver(array=array)

    def _on_groups_event(self, event: Event) -> None:
        self._process_groups_event(event, connect=True)

    def _on_group_nested_list_event(self, event: Event) -> None:
        source_list_event = event.source_list_event
        assert isinstance(source_list_event, Event)
        group_children = source_list_event.source
        assert isinstance(group_children, ParentAware)
        group = group_children.parent
        assert isinstance(group, Group)
        if group_children == group.children:
            self._process_groups_event(source_list_event)

    def _process_groups_event(self, event: Event, connect: bool = False) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type == "inserted":
            if len(self._selected_groups) > 0:
                self._selected_groups.clear()
            else:
                self._update_current_arrays()
            if connect:
                group = event.value
                assert isinstance(group, Group)
                group.nested_list_event.connect(self._on_group_nested_list_event)
        elif event.type == "removed":
            if connect:
                group = event.value
                assert isinstance(group, Group)
                group.nested_list_event.disconnect(self._on_group_nested_list_event)
            if len(self._selected_groups) > 0:
                self._selected_groups.clear()
            else:
                self._update_current_arrays()
        elif event.type == "changed" and isinstance(event.index, int):
            if connect:
                old_group = event.old_value
                assert isinstance(old_group, Group)
                old_group.nested_list_event.disconnect(self._on_group_nested_list_event)
            if len(self._selected_groups) > 0:
                self._selected_groups.clear()
            else:
                self._update_current_arrays()
            if connect:
                group = event.value
                assert isinstance(group, Group)
                group.nested_list_event.connect(self._on_group_nested_list_event)
        elif event.type == "changed":
            if connect:
                old_groups = event.old_value
                assert isinstance(old_groups, List)
                for old_group in old_groups:
                    assert isinstance(old_group, Group)
                    old_group.nested_list_event.disconnect(
                        self._on_group_nested_list_event
                    )
            if len(self._selected_groups) > 0:
                self._selected_groups.clear()
            else:
                self._update_current_arrays()
            if connect:
                groups = event.value
                assert isinstance(groups, List)
                for group in groups:
                    assert isinstance(group, Group)
                    group.nested_list_event.connect(self._on_group_nested_list_event)

    def _on_selected_groups_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type in ("inserted", "removed", "changed"):
            self._update_current_arrays()

    def _on_current_arrays_selection_changed_event(self, event: Event) -> None:
        if self._viewer is not None and not self._updating_current_arrays_selection:
            self._updating_layers_selection = True
            try:
                self._viewer.layers.selection = {
                    array.layer
                    for array in self._current_arrays.selection
                    if array.layer is not None and array.layer in self._viewer.layers
                }
            finally:
                self._updating_layers_selection = False

    def _on_layers_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type == "inserted":
            pass  # ignored intentionally
        elif event.type == "removed":
            layer = event.value
            assert isinstance(layer, Layer)
            array = next(
                (
                    array
                    for group in self._groups
                    for array in group.iter_arrays(recursive=True)
                    if array.layer == layer
                ),
                None,
            )
            if array is not None:
                array.layer = None
        elif event.type == "changed" and isinstance(event.index, int):
            old_layer = event.old_value
            assert isinstance(old_layer, Layer)
            old_array = next(
                (
                    array
                    for group in self._groups
                    for array in group.iter_arrays(recursive=True)
                    if array.layer == old_layer
                ),
                None,
            )
            if old_array is not None:
                old_array.layer = None
            # ignored intentionally
        elif event.type == "changed":
            old_layers = event.old_value
            assert isinstance(old_layers, List)
            for old_layer in old_layers:
                assert isinstance(old_layer, Layer)
                old_array = next(
                    (
                        array
                        for group in self._groups
                        for array in group.iter_arrays(recursive=True)
                        if array.layer == old_layer
                    ),
                    None,
                )
                if old_array is not None:
                    old_array.layer = None
            # ignored intentionally

    def _on_layers_selection_changed_event(self, event: Event) -> None:
        if self._viewer is not None and not self._updating_layers_selection:
            self._updating_current_arrays_selection = True
            try:
                self._current_arrays.selection = {
                    array
                    for layer in self._viewer.layers.selection
                    for array in self._current_arrays
                    if array.layer == layer
                }
            finally:
                self._updating_current_arrays_selection = False

    def _update_current_arrays(self) -> None:
        if len(self._selected_groups) > 0:
            selected_groups = self._selected_groups
        else:
            selected_groups = self._groups
        old_current_arrays = set(self._current_arrays)
        new_current_arrays: Set[Array] = set()
        for group in selected_groups:
            new_current_arrays.update(group.iter_arrays(recursive=True))
        self._current_arrays.selection.clear()
        for array in old_current_arrays.difference(new_current_arrays):
            self._current_arrays.remove(array)
        for array in new_current_arrays.difference(old_current_arrays):
            self._current_arrays.append(array)

    @property
    def pm(self) -> PluginManager:
        return self._pm

    @property
    def viewer(self) -> Optional[Viewer]:
        return self._viewer

    @property
    def groups(self) -> EventedList[Group]:
        return self._groups

    @property
    def selected_groups(self) -> EventedList[Group]:
        return self._selected_groups

    @property
    def current_arrays(self) -> SelectableEventedList[Array]:
        return self._current_arrays


class HierarchicalControllerException(Exception):
    pass


controller = HierarchicalController()