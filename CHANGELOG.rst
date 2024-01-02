===========
 Changelog
===========
All notable changes will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[2.2.4] - 2024-01-02
====================

Fixed
-----
- Loading empty zettels from file system.

[2.2.3] - 2023-03-22
====================

Fixed
-----
- Fixed ICS functions in Zettel.py after running through them in another
  application.

[2.2.2] - 2023-03-19
====================

Fixed
-----
- Fixed printing times for 'event_begin', 'event_end', 'recurring_stop'.

[2.2.1] - 2023-03-18
====================
- Fixed editing select headings in edit_zettels.

[2.2.0] - 2023-03-14
====================
Added ability to initialize new zettels with headings and attributes
loaded from a template. This file defaults to ztemplate.yaml in the
same directory as the new zettel.

Added
-----
- Zettels may now be created with a template.

[2.1.2] - 2023-03-13
====================

Fixed
-----
- Minor bugfix in getMd.

[2.1.1] - 2023-03-13
====================

Fixed
-----
- ``edit_zettels`` now properly updates attributes.

[2.1.0] - 2023-03-13
====================
Each component of a zettel is now optional.

Added
-----
- Titles are now optional.
- Empty zettels are now valid.

Fixed
-----
- Some parsing bugs addressed with more robust unit tests.
- Some typos in docstrings and README.
- Required python version >= 3.7. That's when dicts were ordered by default.

[2.0.0] - 2023-03-09
====================
This release introduces breaking changes to the interface to remove features
that just weren't worth the brain power. Namely the custom functions and tuple
dictionary return from ``edit_zettels``. These proved quickly problematic.

Also introduces new functions to manage zettels on the filesystem, and much
clearer documentation.

Added
-----
- Zettels will now all have a creation_date and zlinks attribute.
- ``edit_zettels`` now has an option to delete zettels if the
  corresponding text was deleted.

- Functions to copy, delete, and move zettels across the filesystem.

Changed
-------
- Reorganization. All filesystem-related functions are in ``editing.py``
  and parsing-related functions are in ``parsing.py``
- ``edit_zettels`` and ``create_zettel`` automatically save changes.
- Rework of unit tests. All tests pass.

Fixed
-----
- Sporadic bugfixes from previous release.

Removed
-------
- Removed SkipZettel exception and ability to pass custom functions.
  Confusing to describe; just edit the list yourself. Much easier.
- Removed "refresh" method from Zettel. Worthless.
- Removed ``filtered_zettels``. Just filter the list using the
  built-in python3 ``filter`` function.

[1.0.2-alpha] - 2023-03-08
==========================
Fixed installation instructions in README.

[1.0.1-alpha] - 2023-03-08
==========================

Added
-----
- Can import important functions directly from libzet.
  eg. ``from libzet import Zettel``

[1.0.0-alpha] - 2023-03-08
==========================
New general flow for using a Zettel.

- ``create_zettel`` to create a new zettel on disk.
- ``load_zettels`` to load a list of zettels from the disk.
- Filter this list based on the needs of your application.
- Send this list to ``edit_zettels`` to edit them in a text editor.
- Use ``save_zettels`` to save the edited zettels back to disk.

Added
-----
- `create_zettel`, `load_zettels`, `edit_zettels`, and `save_zettels`
- Zettels loaded in this manner will have a ``_loadpath`` attr indicating
  where it originally came from.
- Better instructions in README.

Removed
-------
- Dot-operator access for keys within Attributes and zettels. Too restrictive
  to say all keys must match python3 syntax.

[0.1.0-alpha] - 2023-03-01
==========================
Initial release of libzet.

I made this library because 2 of my other applications were doing basically
identical things with zettels so I abstracted out those classes and logic here.

Still needs docs and more robust unit testing, but the interface is solid
because I imported the main functions from a program I've been daily driving
for 2 years (pun intended).

Added
-----
- The main Zettel class. It can load a zettel from markdown or RST documents.
  Each must have a title, and then headings below that followed by a section
  for attributes.
- A function for filtering lists of zettels based on metaprogramming filter
  strings that adhere to python3 syntax.
- It should also be safe to compare against asymmetrical zettels; that is to
  say zettels with mismatched attributes. Attributes not present in particular
  zettels will be ignored (still need to figure out competing types though).
- Attributes class to help with loading and string dumping the attributes back
  to the files. It also automatically parses datetimes out of any field with
  a "date" in it.
