""" Unit tests for the functions in editing.py
"""
import os
import shutil
import unittest

from superdate import parse_date

from libzet import (
    create_zettel, load_zettels, delete_zettels, save_zettels,
    move_zettels, copy_zettels, Zettel)


resources = '{}/resources/fileops-tests'.format(os.path.dirname(__file__))


class TestFileOperations(unittest.TestCase):

    def setUp(self):
        """ Creates the test zettel, so kind of a test of create_zettel.
        """
        os.mkdir(resources)

        path = f'{resources}/basic.md'
        z = create_zettel(
            path, zettel_format='md',
            title='my title', headings={'_notes': 'text'}, no_edit=True)

        self.assertTrue(type(z) is Zettel)
        self.assertTrue(os.path.exists(path))

        self.assertEqual(z.title, 'my title')
        self.assertEqual(z.headings, {'_notes': 'text'})

    def tearDown(self):
        shutil.rmtree(resources)

    def test_load_zettels(self):
        """ Test loading the zettel back.
        """
        z = load_zettels(resources, 'md')
        self.assertEqual(1, len(z))
        self.assertEqual('my title', z[0].title)
        self.assertEqual('text', z[0].headings['_notes'])
        self.assertEqual(f'{resources}/basic.md', z[0].attrs['_loadpath'])

    def test_save_zettels(self):
        """ Make a change and save it
        """
        z = load_zettels(resources, 'md')
        z[0].attrs['greeting'] = 'hello'
        z = save_zettels(z, 'md')

        act = load_zettels(f'{resources}/basic.md', 'md')

        self.assertEqual('hello', act[0].attrs['greeting'])
        self.assertEqual('hello', z[0].attrs['greeting'])

    def test_copy_zettels(self):
        """ Test copying the zettel.
        """
        new_path = f'{resources}/copied.md'
        z = load_zettels(resources, 'md')

        old_path = z[0].attrs['_loadpath']
        z += copy_zettels(z, new_path, 'md')

        self.assertTrue(os.path.exists(old_path))
        self.assertTrue(os.path.exists(new_path))
        self.assertEqual(2, len(z))
        self.assertEqual(f'{resources}/basic.md', z[0].attrs['_loadpath'])
        self.assertEqual(f'{resources}/copied.md', z[1].attrs['_loadpath'])

    def test_delete_zettels(self):
        """ Create and then delete a zettel
        """
        path = f'{resources}/basic.md'
        z = load_zettels(resources, 'md')

        self.assertTrue(os.path.exists(path))
        z = delete_zettels(z)

        self.assertFalse(os.path.exists(path))

    def test_move_zettels(self):
        """ Move a zettel.
        """
        new_path = f'{resources}/moved.md'
        z = load_zettels(resources, 'md')
        old_path = z[0].attrs['_loadpath']
        move_zettels(z, new_path, 'md')

        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(new_path))


if __name__ == '__main__':
    unittest.main()
