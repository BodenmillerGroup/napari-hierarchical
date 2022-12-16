import logging
import os
from typing import List, Optional, Set, Union

from napari._qt.layer_controls.qt_layer_controls_base import QtLayerControls
from napari._qt.layer_controls.qt_layer_controls_container import (
    create_qt_layer_controls,
)
from napari.layers import Layer
from napari.utils.events import Event, EventedList, SelectableEventedList
from napari.viewer import Viewer
from pluggy import PluginManager

from . import hookspecs
from .model import Array, Group
from .utils.parent_aware import ParentAware
from .utils.proxy_image import ProxyImage

PathLike = Union[str, os.PathLike]

logger = logging.getLogger(__name__)


class HierarchicalController:
    def __init__(self) -> None:
        self._pm = PluginManager("napari-hierarchical")
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints("napari-hierarchical")
        self._viewer: Optional[Viewer] = None
        self._proxy_image: Optional[ProxyImage] = None
        self._layer_controls: Optional[QtLayerControls] = None
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
        self._proxy_image = ProxyImage(viewer.layers)
        self._layer_controls = create_qt_layer_controls(self._proxy_image)
        layer_controls_container = viewer.window._qt_window._qt_viewer.controls
        layer_controls_container.widgets[self._proxy_image] = self._layer_controls
        layer_controls_container.addWidget(self._layer_controls)
        viewer.layers.events.connect(self._on_layers_event)
        viewer.layers.selection.events.changed.connect(
            self._on_layers_selection_changed_event
        )

    def can_read_group(self, path: PathLike) -> bool:
        return self._get_group_reader_function(path) is not None

    def read_group(self, path: PathLike) -> Group:
        logger.debug(f"path={path}")
        group_reader_function = self._get_group_reader_function(path)
        if group_reader_function is None:
            raise HierarchicalControllerException(f"No group reader found for {path}")
        try:
            group = group_reader_function(path)
        except Exception as e:
            raise HierarchicalControllerException(e)
        self._groups.append(group)
        return group

    def can_write_group(self, path: PathLike, group: Group) -> bool:
        return self._get_group_writer_function(path, group) is not None

    def write_group(self, path: PathLike, group: Group) -> None:
        logger.debug(f"path={path}, group={group}")
        group_writer_function = self._get_group_writer_function(path, group)
        if group_writer_function is None:
            raise HierarchicalControllerException(f"No group writer found for {path}")
        try:
            group_writer_function(path, group)
        except Exception as e:
            raise HierarchicalControllerException(e)

    def can_load_group(
        self, group: Group, loaded_only: bool = False, unloaded_only: bool = False
    ) -> bool:
        return all(
            self.can_load_array(array)
            for array in group.iter_arrays(recursive=True)
            if (not loaded_only or array.loaded)
            and (not unloaded_only or not array.loaded)
        )

    def load_group(self, group: Group) -> None:
        logger.debug(f"group={group}")
        for array in group.iter_arrays(recursive=True):
            if not array.loaded:
                self.load_array(array)

    def unload_group(self, group: Group) -> None:
        logger.debug(f"group={group}")
        for array in group.iter_arrays(recursive=True):
            if array.loaded:
                self.unload_array(array)

    def can_load_array(self, array: Array) -> bool:
        return self._get_array_loader_function(array) is not None

    def load_array(self, array: Array) -> None:
        assert self._viewer is not None
        if array.loaded:
            raise HierarchicalControllerException(
                f"Array has already been loaded: {array}"
            )
        logger.debug(f"array={array}")
        array_loader_function = self._get_array_loader_function(array)
        if array_loader_function is None:
            raise HierarchicalControllerException(f"No array loader found for {array}")
        try:
            array_loader_function(array)
        except Exception as e:
            raise HierarchicalControllerException(e)
        assert array.layer is not None
        self._viewer.add_layer(array.layer)

    def unload_array(self, array: Array) -> None:
        logger.debug(f"array={array}")
        if array.layer is None:
            raise HierarchicalControllerException(f"Array has not been loaded: {array}")
        if self._viewer is not None and array.layer in self._viewer.layers:
            self._viewer.layers.remove(array.layer)
        array.layer = None

    def can_save_group(self, group: Group) -> bool:
        return not group.dirty and all(
            self.can_save_array(array)
            for array in group.iter_arrays(recursive=True)
            if array.loaded
        )

    def save_group(self, group: Group) -> None:
        logger.debug(f"group={group}")
        if group.dirty:
            raise HierarchicalControllerException(
                f"Group structure has been modified: {group}"
            )
        for array in group.iter_arrays(recursive=True):
            if array.loaded:
                self.save_array(array)

    def can_save_array(self, array: Array) -> bool:
        return self._get_array_saver_function(array) is not None

    def save_array(self, array: Array) -> None:
        logger.debug(f"array={array}")
        if not array.loaded:
            raise HierarchicalControllerException(f"Array is not loaded: {array}")
        array_saver_function = self._get_array_saver_function(array)
        if array_saver_function is None:
            raise HierarchicalControllerException(f"No array saver found for {array}")
        try:
            array_saver_function(array)
        except Exception as e:
            raise HierarchicalControllerException(e)

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
        group_arrays_or_children = source_list_event.source
        assert isinstance(group_arrays_or_children, ParentAware)
        group = group_arrays_or_children.parent
        assert isinstance(group, Group)
        if group_arrays_or_children == group.children:
            self._process_groups_event(source_list_event)
        elif group_arrays_or_children == group.arrays:
            self._process_arrays_event(source_list_event)

    def _process_groups_event(self, event: Event, connect: bool = False) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type == "inserted":
            logger.debug(f"event={event.type}")
            if len(self._selected_groups) > 0:
                self._selected_groups.clear()
            else:
                self._update_current_arrays()
            if connect:
                group = event.value
                assert isinstance(group, Group)
                group.nested_list_event.connect(self._on_group_nested_list_event)
        elif event.type == "removed":
            logger.debug(f"event={event.type}")
            if connect:
                group = event.value
                assert isinstance(group, Group)
                group.nested_list_event.disconnect(self._on_group_nested_list_event)
            if len(self._selected_groups) > 0:
                self._selected_groups.clear()
            else:
                self._update_current_arrays()
        elif event.type == "changed" and isinstance(event.index, int):
            logger.debug(f"event={event.type}")
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
            logger.debug(f"event={event.type}")
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

    def _process_arrays_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type in ("inserted", "removed", "changed"):
            logger.debug(f"event={event.type}")
            self._update_current_arrays()

    def _on_selected_groups_event(self, event: Event) -> None:
        if not isinstance(event.sources[0], EventedList):
            return
        if event.type in ("inserted", "removed", "changed"):
            logger.debug(f"event={event.type}")
            self._update_current_arrays()

    def _on_current_arrays_selection_changed_event(self, event: Event) -> None:
        if self._viewer is not None and not self._updating_current_arrays_selection:
            logger.debug("")
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
            logger.debug(f"event={event.type}")
            pass  # ignored intentionally
        elif event.type == "removed":
            logger.debug(f"event={event.type}")
            layer = event.value
            assert isinstance(layer, Layer)
            array = next(
                (
                    array
                    for group in self._groups
                    for array in group.iter_arrays(recursive=True)
                    if array.layer is not None and array.layer == layer
                ),
                None,
            )
            if array is not None:
                array.layer = None
        elif event.type == "changed" and isinstance(event.index, int):
            logger.debug(f"event={event.type}")
            old_layer = event.old_value
            assert isinstance(old_layer, Layer)
            old_array = next(
                (
                    array
                    for group in self._groups
                    for array in group.iter_arrays(recursive=True)
                    if array.layer is not None and array.layer == old_layer
                ),
                None,
            )
            if old_array is not None:
                old_array.layer = None
            # ignored intentionally
        elif event.type == "changed":
            logger.debug(f"event={event.type}")
            old_layers = event.old_value
            assert isinstance(old_layers, List)
            for old_layer in old_layers:
                assert isinstance(old_layer, Layer)
                old_array = next(
                    (
                        array
                        for group in self._groups
                        for array in group.iter_arrays(recursive=True)
                        if array.layer is not None and array.layer == old_layer
                    ),
                    None,
                )
                if old_array is not None:
                    old_array.layer = None
            # ignored intentionally

    def _on_layers_selection_changed_event(self, event: Event) -> None:
        assert self._viewer is not None
        if len(self._viewer.layers.selection) > 1:
            assert self._layer_controls is not None
            layer_controls_container = (
                self._viewer.window._qt_window._qt_viewer.controls
            )
            layer_controls_container.setCurrentWidget(self._layer_controls)
        if not self._updating_layers_selection:
            logger.debug("")
            self._updating_current_arrays_selection = True
            try:
                self._current_arrays.selection = {
                    array
                    for layer in self._viewer.layers.selection
                    for array in self._current_arrays
                    if array.layer is not None and array.layer == layer
                }
            finally:
                self._updating_current_arrays_selection = False

    def _update_current_arrays(self) -> None:
        logger.debug("")
        if len(self._selected_groups) > 0:
            selected_groups = self._selected_groups
        else:
            selected_groups = self._groups
        old_current_arrays = set(self._current_arrays)
        new_current_arrays: Set[Array] = set()
        for group in selected_groups:
            new_current_arrays.update(group.iter_arrays(recursive=True))
        for array in old_current_arrays.difference(new_current_arrays):
            self._current_arrays.remove(array)
        for array in new_current_arrays.difference(old_current_arrays):
            self._current_arrays.append(array)
        self._current_arrays.selection.clear()

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
