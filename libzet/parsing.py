""" Functions to parse Zettels out of text

Zettels may be parsed out of RST or Markdown text.

The main functions to consider are str_to_zettels and zettels_to_str.
"""
import os

from libzet import Zettel


rst_sep = '.. end-zettel'
md_sep = '<!--- end-zettel --->'


def str_to_zettels(text, zettel_format):
    """ Convert a str to a list of zettels.

    This function's return may be passed to zettels_to_str.

    Args:
        text: Text to convert to zettels.
        zettel_format: 'rst' or 'md'.

    Returns:
        A list of Zettel references.

    Raises:
        ValueError if the text was invalid.
    """
    zettels = []
    if zettel_format == 'rst':
        zettels = get_zettels_from_rst(text)
    elif zettel_format == 'md':
        zettels = get_zettels_from_md(text)

    return zettels


def zettels_to_str(zettels, zettel_format, headings=None):
    """ Return many zettels as a str.

    This function's return may be passed to str_to_zettels.

    Args:
        zettels: List of zettels to print.
        zettel_format: 'rst' or 'md'.
        headings: Only print select headings.

    Returns:
        A str representing the zettels.
    """
    text = ''
    formats = ['rst', 'md']

    if zettel_format not in formats:
        raise ValueError(f'zettel_format must be in {formats}')

    if zettel_format == 'rst':
        text = [x.getRst(headings) for x in zettels]
        text = f'\n{rst_sep}\n\n\n'.join(sorted([x for x in text if x]))
    elif zettel_format == 'md':
        text = [x.getMd(headings) for x in zettels]
        text = f'\n{md_sep}\n\n\n'.join(sorted([x for x in text if x]))

    return text


def get_zettels_from_md(md):
    """ Parse many zettels out of markdown text.

    Zettels are separated by md_sep

    Args:
        md: MD text or file to parse.

    Returns:
        List of zettels parsed from the string.

    Raises:
        ValueError if the text was invalid.
    """
    if os.path.exists(md):
        with open(md) as f:
            md = f.read()

    md = md.strip()
    if not md:
        return []

    # Markdown zettels are terminated by a line containing only this string.
    texts = md.split(md_sep)
    if not texts[-1]:
        texts.pop()

    zettels = []

    for t in texts:
        zettels.append(Zettel.createFromMd(t))

    return zettels


def get_zettels_from_rst(rst):
    """ Parse many zettels out of rst text.

    Zettels are separated by rst_sep

    Args:
        md: MD text or file to parse.

    Returns:
        List of zettels parsed from the string.

    Raises:
        ValueError if the text was invalid.
    """
    if os.path.exists(rst):
        with open(rst) as f:
            rst = f.read()

    rst = rst.strip()
    if not rst:
        return []

    texts = rst.split(rst_sep)
    if not texts[-1]:
        texts.pop()

    zettels = []
    for t in texts:
        zettels.append(Zettel.createFromRst(t))

    return zettels
