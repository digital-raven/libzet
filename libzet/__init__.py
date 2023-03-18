import sys

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

__version__ = metadata.version('libzet')


# Official functions should be directly importable from libzet.
from libzet.Attributes import Attributes
from libzet.Zettel import Zettel
from libzet.editing import (
    load_zettels, save_zettels, delete_zettels,
    create_zettel, edit_zettels,
    move_zettels, copy_zettels)

from libzet.parsing import str_to_zettels, zettels_to_str
