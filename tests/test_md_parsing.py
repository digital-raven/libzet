import os
import unittest

from superdate import parse_date, SuperDate

from libzet import Zettel
from libzet.parsing import str_to_zettels, zettels_to_str


resources = '{}/resources'.format(os.path.dirname(__file__))


def _generate_input(text):
    return '\n'.join(['    '.join(l_.split('    ')[2:]) for l_ in text.splitlines()])


# dictionary of strings to parse and expected zettel data
inputs = [
    {
        'text': _generate_input(""),
        'exp': Zettel(
            title='',
            headings={},
            attrs={'creation_date': 'today', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        """),
        'exp': Zettel(
            title='',
            headings={},
            attrs={'creation_date': 'today', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        # my title
        """),
        'exp': Zettel(
            title='my title',
            headings={},
            attrs={'creation_date': 'today', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        # my title


        content


        """),
        'exp': Zettel(
            title='my title',
            headings={'_notes': '\n\ncontent'},
            attrs={'creation_date': 'today', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        # my title

        content

        <!--- attributes --->
            ---
            greeting: hello
        """),
        'exp': Zettel(
            title='my title',
            headings={'_notes': '\ncontent\n'},
            attrs={'creation_date': 'today', 'greeting': 'hello', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        no title
        <!--- attributes --->
            ---
            greeting: hello
        """),
        'exp': Zettel(
            title='',
            headings={'_notes': 'no title'},
            attrs={'creation_date': 'today', 'greeting': 'hello', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        no title

        ## heading 1

        but a heading


        <!--- attributes --->
            ---
            greeting: hello
        """),
        'exp': Zettel(
            title='',
            headings={'_notes': 'no title\n', 'heading 1': '\nbut a heading\n\n'},
            attrs={'creation_date': 'today', 'greeting': 'hello', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        ## heading 1

        but a heading


        ## heading 2
        heading2 text
        <!--- attributes --->
            ---
            greeting: hello
        """),
        'exp': Zettel(
            title='',
            headings={
                'heading 1':
                '\nbut a heading\n\n',
                'heading 2': 'heading2 text'},
            attrs={'creation_date': 'today', 'greeting': 'hello', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        just content
        """),
        'exp': Zettel(
            title='',
            headings={'_notes': 'just content'},
            attrs={'creation_date': 'today', 'zlinks': {}}),
    },
    {
        'text': _generate_input("""
        <!--- attributes --->
            ---
            greeting: hello
        """),
        'exp': Zettel(
            title='',
            headings={},
            attrs={'creation_date': 'today', 'greeting': 'hello', 'zlinks': {}}),
    },
]


class TestMdParsing(unittest.TestCase):

    def test_md_parsing(self):
        """ Test each of the configurations

        In each, the titles, headings, and attrs should match. Heading
        order should be preserved, and any key with a 'date' in it should
        parse as a SuperDate
        """
        for i, d in enumerate(inputs):
            parsed = Zettel.createFromMd(d['text'])
            self.assertEqual(d['exp'].title, parsed.title)
            self.assertEqual(d['exp'].headings, parsed.headings)
            self.assertEqual(d['exp'].attrs, parsed.attrs)
            self.assertEqual(list(d['exp'].headings.keys()), list(parsed.headings.keys()))

            date_keys = [k for k in parsed.attrs if 'date' in k]
            for k in date_keys:
                self.assertIs(SuperDate, type(parsed.attrs[k]))


if __name__ == '__main__':
    unittest.main()
