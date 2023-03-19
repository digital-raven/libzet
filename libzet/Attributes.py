import datetime
import yaml

from superdate import SuperDate

from libzet.NoCompare import NoCompare


class Attributes(dict):
    """ Class to hold a Zettel's metadata.

    If a non-existent key is queried then a NoCompare is returned.
    """
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @classmethod
    def fromYaml(cls, s):
        """ Load Attributes from yaml.

        Args:
            s: String or filename of yaml to init from.

        Raises:
            FileNotFoundError or PermissionError if yaml was a file and
                couldn't be read.

            Whatever yaml.safe_load raises.
        """
        d = yaml.safe_load(s)
        if type(d) is str:
            with open(s) as f:
                s = f.read()
            d = yaml.safe_load(s)

        return Attributes(d)

    def toYamlDict(self):
        """ Dump this object as a yaml string.

        Reverses SuperDate values to easymode yaml str.

            yaml.dump(attributes.toYamlDict)

        Returns:
            A dictionary that yaml can dump.
        """
        d = dict()
        d.update(self)
        dtfields = ['event_begin', 'event_end', 'recurring_stop']

        for k, v in d.items():
            if v and (k in dtfields or 'date' in k):
                if type(v._date) is datetime.date:
                    d[k] = v.strftime('%Y-%m-%d, %a')
                if type(v._date) is datetime.datetime:
                    d[k] = v.strftime('%Y-%m-%d, %a, %H:%M')

        return d

    def __str__(self):
        return '---\n' + yaml.dump(self.toYamlDict())

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return NoCompare()

    def __setitem__(self, key, val):
        """ Keys must be python3 identifiers.

        Will also perform special parsing logic for keys that contain
        the word "date".
        """
        dtfields = ['event_begin', 'event_end', 'recurring_stop']
        if val and (key in dtfields or 'date' in key):
            val = SuperDate(val)

        dict.__setitem__(self, key, val)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
