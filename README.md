# napari-bioimage

[![License MIT](https://img.shields.io/pypi/l/napari-bioimage.svg?color=green)](https://github.com/BodenmillerGroup/napari-bioimage/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-bioimage.svg?color=green)](https://pypi.org/project/napari-bioimage)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-bioimage.svg?color=green)](https://python.org)
[![tests](https://github.com/BodenmillerGroup/napari-bioimage/workflows/tests/badge.svg)](https://github.com/BodenmillerGroup/napari-bioimage/actions)
[![codecov](https://codecov.io/gh/BodenmillerGroup/napari-bioimage/branch/main/graph/badge.svg)](https://codecov.io/gh/BodenmillerGroup/napari-bioimage)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-bioimage)](https://napari-hub.org/plugins/napari-bioimage)

Complex bio-image file format support for napari

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.


## Description

This plugin adds the following concepts to napari:

- *Images* are hierarchically organized collections of layers
  - Images can correspond to a physical file on disk
  - Images may contain "child images" --> image trees
  - The (user-editable) image trees are shown in the *Images* panel
  - Reading an image means loading its tree (added as a "root node", without loading data)
  - Writing an image means creating an image container on disk and saving all associated layers to it
  - Selecting an image selects all layers associated with its (sub-)tree
- *Layers* are viewable objects (cf. original napari layers, e.g. images, labels)
  - Every layer belongs to an image (no direct correspondence to physical files on disk)
  - "Anonymous layers" (cf. original napari layers) are assigned to a "New Image" upon creation
  - Layers can be loaded/saved independently from/to images ("lazy reading/writing of images")
  - Layers may be moved from one image to another in memory by the user
- Layers are *grouped* by layer metadata (flat groupings across all images, e.g. by channel/label label name)
  - Layer groupings are shown in the *Layers* panel, containing one tab for each metadata grouping (key)
  - An additional grouping (tab) exists for Layer identity ("Layer" tab, cf. original napari Layers panel)
  - Reading/writing a layer group means reading/writing all its layers
  - Selecting a layer group selects all its layers


## Installation

You can install `napari-bioimage` via [pip]:

    pip install "napari-bioimage[all]"

To install latest development version :

    pip install "git+https://github.com/BodenmillerGroup/napari-bioimage.git#egg=napari-bioimage[all]"


## Implementation

This plugin implements reader, writer, and widget functionality. The reader reads an image (not actual image data, see description above) and opens the `QImagesWidget` and `QLayersWidget` widgets in `napari_bioimage.widgets`. The writer writes the selected layers (not the entire image, see description above). All operations are done through the `napari_bioimage.controller` singleton instance, which "extends" the functionality of `napari.viewer.Viewer`.

Image readers/writers are implemented as plugins using [pluggy](https://pluggy.readthedocs.io), similar to the [first-generation napari plugin engine](https://github.com/napari/napari-plugin-engine). Out of the box, this plugin ships with readers/writers for HDF5, Zarr, OME-Zarr, and imaging mass cytometry (IMC) file formats, implemented in `napari_bioimage.contrib`. Additionally, the plugin also provides sample data for these file formats.

The hierarchical image/layer model (composite tree pattern) is implemented in `napari_bioimage.model`. For consistency with the original napari layer model, all model classes inherit from `napari.utils.events.EventedModel`. This renders the creation of lazy models (e.g. for representing the whole file system) impossible, which is intended. Despite implementing a composite tree pattern, the model classes do not inherit from `napari.utils.tree` to avoid problems due to multiple inheritance/pydantic.

The Qt tree model is implemented in `napari_bioimage.widgets.QImageTreeModel`. For listening to model changes, due to [problems with propagating events in nested EventedModel/EventedList hierarchies](https://napari.zulipchat.com/#narrow/stream/212875-general/topic/.E2.9C.94.20model.20events.20propagation), individual event handlers need to be registered for each ImageGroup instance. Until this issue gets resolved, as a workaround, the callback references are stored directly in `napari_bioimage.model.ImageGroup`.

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.


## License

Distributed under the terms of the [MIT] license,
"napari-bioimage" is free and open source software


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

[file an issue]: https://github.com/BodenmillerGroup/napari-bioimage/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
