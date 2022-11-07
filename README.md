# napari-dataset

[![License MIT](https://img.shields.io/pypi/l/napari-dataset.svg?color=green)](https://github.com/BodenmillerGroup/napari-dataset/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-dataset.svg?color=green)](https://pypi.org/project/napari-dataset)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-dataset.svg?color=green)](https://python.org)
[![tests](https://github.com/BodenmillerGroup/napari-dataset/workflows/tests/badge.svg)](https://github.com/BodenmillerGroup/napari-dataset/actions)
[![codecov](https://codecov.io/gh/BodenmillerGroup/napari-dataset/branch/main/graph/badge.svg)](https://codecov.io/gh/BodenmillerGroup/napari-dataset)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-dataset)](https://napari-hub.org/plugins/napari-dataset)

Complex dataset support for napari

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.


## Description

This plugin adds the following concepts to napari:

- *Datasets* are collections of layers
  - Datasets may correspond to a file (on disk, in the cloud, ...)
  - Datasets may contain child datasets (hierarchies, cf. HDF5/Zarr)
  - Reading a dataset: load the hierarchy from the corresponding file
  - Writing a dataset: create a file and save all associated layers to it
  - Selecting a dataset: select all layers associated with the dataset or its children
  - Layers can be separately loaded from/saved to datasets
- Layers are *grouped* by reader-defined metadata (e.g. channel/label name)
  - Layers are grouped across all datasets (flat groupings)
  - Each grouping is shown in a separate tab in the layers panel
  - The "Layer" tab groups layers by their identity (cf. original napari Layers panel)
  - Reading/writing a layer group: save/load all layers in the group
  - Selecting a layer group: select all layers in the group


## Installation

You can install `napari-dataset` via [pip]:

    pip install "napari-dataset[all]"

To install latest development version :

    pip install "git+https://github.com/BodenmillerGroup/napari-dataset.git#egg=napari-dataset[all]"


## Implementation

This plugin implements reader, writer, and widget functionality. The reader reads a dataset (not actual image data, see description above) and opens the `QDatasetsWidget` and `QLayersWidget` widgets in `napari_dataset.widgets`. The writer writes the selected layers (not the entire dataset, see description above). All operations are done through the `napari_dataset.controller` singleton instance, which "extends" the functionality of `napari.viewer.Viewer`.

Dataset readers/writers are implemented as plugins using [pluggy](https://pluggy.readthedocs.io), similar to the [first-generation napari plugin engine](https://github.com/napari/napari-plugin-engine). Out of the box, this plugin ships with readers/writers for HDF5, Zarr, OME-Zarr, and imaging mass cytometry (IMC) file formats, implemented in `napari_dataset.contrib`. Additionally, the plugin also provides sample data for these file formats.

The hierarchical dataset/layer model (composite tree pattern) is implemented in `napari_dataset.model`. For consistency with the original napari layer model, all model classes inherit from `napari.utils.events.EventedModel`. This renders the creation of lazy models (e.g. for representing the whole file system) impossible, which is intended. Despite implementing a composite tree pattern, the model classes do not inherit from `napari.utils.tree` to avoid problems due to multiple inheritance/pydantic.

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.


## License

Distributed under the terms of the [MIT] license,
"napari-dataset" is free and open source software


## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/BodenmillerGroup/napari-dataset/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
