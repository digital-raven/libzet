import os
import unittest
from datetime import datetime

from superdate import parse_date

from libzet import Attributes, Zettel
from libzet.parsing import get_zettels_from_md, get_zettels_from_rst


resources = '{}/resources'.format(os.path.dirname(__file__))


class TestZettel(unittest.TestCase):

    def test_rst_creation_and_str_back(self):
        """ Basic rst creation
        """
        with open(f'{resources}/rst/basic.rst') as f:
            exp = f.read()

        z = Zettel.createFromRst(exp)

        self.assertEqual(exp, z.getRst())
        self.assertIs(Attributes, type(z.attrs))
        self.assertTrue(z.attrs['creation_date'] == datetime(2022, 4, 19))

    def test_md_creation_and_str_back(self):
        """ Basic MD creation.
        """
        path = f'{resources}/md/basic.md'
        z = Zettel.createFromMd(path)

        with open(path) as f:
            exp = f.read()

        self.assertEqual(exp, z.getMd())
        self.assertIs(Attributes, type(z.attrs))
        self.assertTrue(z.attrs['creation_date'] == datetime(2022, 4, 19))

    def test_alphabetized_attributes(self):
        """ Zettels should alphabetize attributes when printing.
        """
        z = Zettel.createFromRst(f'{resources}/rst/out-of-order.rst')
        z = Zettel.createFromRst(z.getRst())
        keys = sorted(z.attrs)
        self.assertEqual(keys, list(z.attrs.keys()))

    def test_trailing_space(self):
        """ Zettel parsing should trim trailing spaces.
        """
        z = Zettel.createFromRst(f'{resources}/rst/trailing-lines.rst')
        with open(f'{resources}/rst/trailing-lines.rst') as f:
            exp = f.read().strip() + '\n'

        self.assertEqual(exp, z.getRst())


if __name__ == '__main__':
    unittest.main()
