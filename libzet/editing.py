""" Functions to assist loading, editing, and saving zettels.
"""
import os
import shutil
import yaml

from libzet.Attributes import Attributes
from libzet.util.edit import edit
from libzet.parsing import str_to_zettels, zettels_to_str
from libzet.Zettel import Zettel


def create_zettel(
        path,
        text='', title='', headings=None, attrs=None, zettel_format='md',
        no_edit=False, errlog='', template=None):
    """ Create and new zettel on disk and edit it.

    Args:
        path: Path to create new zettel.
        text: Provide a body of text from which to parse the whole zettel.
        headings: Headings to create the new zettel with.
        attrs: Default attributes to create the zettel.
        zettel_format: 'md' or 'rst'
        errlog: See edit_zettels
        no_edit: Set to True to skip editing.
        template: Optionally init the new zettel from a template. May be
            a path to a yaml file or a dict. Defaults to ztemplate.yaml
            within the same dir as the new zettel.

            If template exists then the headings and attrs from that
            file will be used to init the zettel.

    Returns:
        The new zettel reference.

    Raises:
        FileExistsError: There was already a zettel at path.
        ValueError: The newly created zettel was invalid.
    """
    if os.path.exists(path):
        raise FileExistsError(f'Already a Zettel at {path}')

    if template is None:
        dir_ = os.path.dirname(path) or '.'
        template = template or f'{dir_}/ztemplate.yaml'

    if type(template) is str:
        if os.path.exists(template):
            with open(template) as f:
                template = yaml.safe_load(f.read())
        else:
            template = {}

    template = template or {}
    template = Attributes(template)

    # Set defaults from template
    if 'headings' in template and not headings:
        headings = {k: '' for k in template['headings']}

    if 'attrs' in template and not attrs:
        attrs = template['attrs']

    z = None
    if text:
        z = str_to_zettels(text, zettel_format)[0]
    else:
        z = Zettel(title, headings, attrs)

    z.attrs['_loadpath'] = path

    if not no_edit:
        edit_zettels([z], zettel_format, headings, errlog)
    else:
        save_zettels([z], zettel_format)

    return z


def load_zettels(paths, zettel_format='md', recurse=False):
    """ Load Zettels from the filesystem.

    Zettels will be updated with a _loadpath value in their attrs.
    Send these zettels to save_zettels after modifying them to write
    them to disk. The _loadpath attribute will not be written back to disk.

    Args:
        paths: Path or list paths to zettels. Each may be a dir or file.
        zettel_format: md or rst
        recurse: True to recurse into subdirs, False otherwise.

    Returns:
        A list of zettels.

        This list may be passed to save_zettels to write
        them to the filesystem.

    Raises:
        OSError if one of the files couldn't be opened.
        ValueError if one of the zettels contained invalid text.
    """
    zettels = []

    if type(paths) is not list:
        paths = [paths]

    for path in paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f'{path} does not exist.')

        if os.path.isdir(path):
            root, dir_, files = readdir_(path)

            files = [f'{root}/{f}' for f in files if f.endswith(f'.{zettel_format}')]

            for f in files:
                zettels.append(_load_zettel(f, zettel_format))

            if recurse:
                for d in dir_:
                    zettels.extend(load_zettels(f'{root}/{d}', zettel_format, recurse))

        elif os.path.isfile(path):
            zettels.append(_load_zettel(path, zettel_format))

        else:
            raise ValueError(f'{path} is not a regular file or directory.')

    return zettels


def edit_zettels(zettels, zettel_format='md', headings=None, errlog='', delete=False):
    """ Bulk edit zettels provided by load_zettels.

    Delete the text for a zettel to avoid updating it.

    It is possible to add new zettels while editing, just be sure
    to set the _loadpath attribute for each new zettel.

    Args:
        zettels: List of zettels to edit.
        zettel_format: md or rst.
        headings: List of select headings edit for each zettel.
        errlog: Write your working text to this location if parsing failed.
        delete: If True, then zettels whose text is deleted during editing will
            also be deleted from the disk.

    Returns:
        A list of zettels that were updated. Deleted zettels will not be
        in this list.

    Raises:
        ValueError if any zettels were edited in an invalid way.
    """
    if type(zettels) is not list:
        zettels = [zettels]

    if any(['_loadpath' not in z.attrs for z in zettels]):
        raise ValueError('Some zettels are missing a _loadpath')

    orig = {z.attrs['_loadpath']: z for z in zettels}

    if headings:
        [z.headings.setdefault(h, '') for z in orig.values() for h in headings]

    # Edit and parse-back.
    s = zettels_to_str(zettels, zettel_format, headings)
    s = edit(s)

    try:
        updates = str_to_zettels(s, zettel_format)
    except ValueError as e:
        if errlog:
            with open(errlog, 'w') as f:
                f.write(s)
        raise

    # Make sure everyone still has a _loadpath
    if any(['_loadpath' not in z.attrs for z in updates]):
        if errlog:
            with open(errlog, 'w') as f:
                f.write(s)

        raise ValueError('Some zettels are missing a _loadpath')

    updates = {z.attrs['_loadpath']: z for z in updates}

    # Record changes.
    modified = []
    deleted = []

    for k, z in updates.items():
        if k in orig:
            modified.append(orig[k])
            modified[-1].update(z, headings)
        else:
            modified.append(z)

    for k, z in orig.items():
        if k not in updates:
            deleted.append(z)

    # Optionally delete zettels
    save_zettels(modified, zettel_format)
    if delete:
        delete_zettels(deleted)

    return modified


def save_zettels(zettels, zettel_format='md'):
    """ Save zettels back to disk.

    Args:
        zettels: List of zettels.
        zettel_format: md or rst.

    Returns:
        The list of zettels as saved to disk.

    Raises:
        KeyError if a zettel is missing a _loadpath attribute. No zettels
            will be written to disk if this is the case.

        OSError if a zettel's text couldn't be written to disk.
    """
    if type(zettels) is not list:
        zettels = [zettels]

    if any(['_loadpath' not in z.attrs for z in zettels]):
        raise KeyError('All zettels need a _loadpath to save.')

    for z in zettels:
        loadpath = z.attrs['_loadpath']
        del(z.attrs['_loadpath'])
        try:
            with open(loadpath, 'w') as f:
                f.write(zettels_to_str([z], zettel_format))
        finally:
            z.attrs['_loadpath'] = loadpath

    return zettels


def delete_zettels(zettels):
    """ Delete zettels from the filesystem.

    Args:
        zettels: Zettels to delete. Must have a _loadpath attribute.

    Returns:
        An empty list to represent the loss of these zettels

    Raises:
        KeyError if any zettels were missing a _loadpath. No zettels
            will be deleted in this case.

        OSError if the zettel could not be deleted.
    """
    if type(zettels) is not list:
        zettels = [zettels]

    if any(['_loadpath' not in z.attrs for z in zettels]):
        raise KeyError('All zettels need a _loadpath to delete.')

    [os.remove(z.attrs['_loadpath']) for z in zettels]
    return []


def copy_zettels(zettels, dest, zettel_format='md'):
    """ Copy zettels to a new file location.

    Zettels are saved to disk before copying.

    Args:
        zettels: List of zettels to copy.
        zettel_format: md or rst.
        dest: Location to copy them to.

    Returns:
        A list of the new zettels loaded from their new file locations.

    Raises:
        KeyError if any zettels were missing a _loadpath. No zettels
            will be written to disk in this case.

        OSError if any of the zettels failed to copy.

        See shutil.copy
    """
    if type(zettels) is not list:
        zettels = [zettels]

    if any(['_loadpath' not in z.attrs for z in zettels]):
        raise KeyError('All zettels need a _loadpath to copy.')

    # Save first to sync up.
    save_zettels(zettels, zettel_format)

    # Copy raw files
    newzets = [shutil.copy(z.attrs['_loadpath'], dest) for z in zettels]

    # Load and return the new zettels
    newzets = load_zettels(newzets, zettel_format)
    return newzets


def move_zettels(zettels, dest, zettel_format='md'):
    """ Move zettels. Zettels will be saved before moving.

    The zettels will be deleted from their former paths which
    invalidates their previous _loadpath. Use this function like...

        zettels = move_zettels(zettels, './new-dir/')

    Args:
        zettels: List of zettels to move.
        zettel_format: md or rst.
        dest: Destination directory.

    Returns:
        A list of the zettels from their new home.

    Raises:
        See copy_zettels and delete_zettels.
    """
    newzets = copy_zettels(zettels, dest, zettel_format)
    delete_zettels(zettels)
    return newzets


# Helper functions below here
def readdir_(d):
    """ Same as OS. walk executed at the first level.

    Returns:
        A 3-tuple. First entry is the root (d), second is a list of all
        directory entries within d, and the third is a list of names of
        regular files.
    """
    d = d.rstrip(os.path.sep)
    if not os.path.isdir(d):
        raise ValueError('"{}" is not a directory.'.format(d))

    for root, dirs, files in os.walk(d):
        return root, dirs, files


def _load_zettel(path, zettel_format='md'):
    """ Load a single Zettel from the filesystem.

    The zettel will gain a new _loadpath attribute. Useful to
    know where to write it back.

    Args:
        path: Path to zettel.
        zettel_format: rst or md.
        fun: Call this function on the zettel as it's loaded from disk.
            Raise SkipZettel from fun to avoid loading a zettel.

    Returns:
        A reference to the newly loaded zettel.
    """
    with open(path) as f:
        z = str_to_zettels(f.read(), zettel_format)[0]

    # Guarantee _loadpath
    z.attrs['_loadpath'] = path
    return z
