import os
import yaml
from datetime import timedelta, datetime

from icalendar import Event
from superdate import parse_date

from libzet.Attributes import Attributes


def parse_duration(duration):
    """ Return a timedelta from a duration str.

    Can handle humanized durations. Like "40min" or "1 hour". Handles
    down to minute precision.

    Args:
        duration: Duration to turn into timedelta.

    Returns:
        timedelta object.

    Raises:
        ValueError if parsing the duration fails.
    """
    if type(duration) is timedelta:
        return duration

    later = parse_date(duration)
    now = datetime.now()
    now = datetime(now.year, now.month, now.day, now.hour, now.minute)

    return later - now


def parse_rrule(rrule):
    """ Parse an icalendar rrule str into a dict.

    Follow the ICS convention for rrules.

    https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html

    But omit the leading "RRULE:".

    Use the return of this function like this.

        event['rrule'] = parse_rrule(some_rrule))

    Arg:
        rrule: The str rrule to parse.

    Returns:
        An rrule object that can be directly set as an icalendar.Event's
        'rrule' index.

    Raises:
        ValueError if the rrule str wasn't valid.
    """
    rrule = 'RRULE:' + rrule
    s = '\n'.join(['BEGIN:VEVENT', rrule, 'END:VEVENT'])
    event = Event.from_ical(s)

    if not len(event['rrule']):
        raise ValueError('Invalid rrule')

    return event['rrule']


# Find heading points.
def _is_rst_heading(s):
    s = s.strip()
    return s.startswith('=') and s.endswith('=')


def _is_md_heading(s):
    s = s.lstrip()
    return s.startswith('## ')


class Zettel:
    """ Represents a zettel.
    """
    def __init__(self, title, headings=None, attrs=None, **kwargs):
        """ Init a new Zettel.

        All zettels will have a creation_date and zlinks dictionary where
        the keys are link types and values are the links themselves.

        Args:
            title: Title of the zettel.
            headings: Dictionary of subheadings. Each heading is paired with
                a string for its zettel.

            attrs: Metadata about the zettel.

                Attributes may also be provided to the constructor via
                keyword arguments.

        Raises:
            Loading the attributes may raise ValueError. See the Attributes
            class for why this might happen.
        """
        headings = headings or dict()
        attrs = attrs or dict()

        self.title = title
        self.headings = {k: v for k, v in headings.items()}

        # Process attrs
        self.attrs = Attributes()
        self.attrs.update(attrs)
        self.attrs.update(kwargs)

        if 'creation_date' not in self.attrs:
            self.attrs['creation_date'] = parse_date('today')

        if 'zlinks' not in self.attrs:
            self.attrs['zlinks'] = dict()

    def asIcsEvent(self, uid):
        """ Return an icalendar.Event class from this Zettel's data.

        A zettel must have either a event_begin or a due_date to be
        considered capable of turning into an ICS Event.

        This function does not support all ICS Event values. The
        supported values are...
        - uid
        - dtstamp: Initialized to the time this method was called.
        - summary
        - description
        - dtstart: as event_begin or due_date with respective *_time's
        - dtend: as event_end + end_time (optional)
        - rrule: as recurring

        Returns:
            An icalendar.Event created from this instance's data. If
            this zettel doesn't have a due_date or event_begin field then
            None will be returned.

        Raises:
            ValueError if "recurring" was an invalid rrule or if parsing
            the "duration" attr failed.
        """
        exp = ['event_begin', 'due_date']
        if not any([x in self.attrs and self.attrs[x] for x in exp]):
            return None

        desc = self.headings['_notes'] if '_notes' in self.headings else ''

        event = Event()
        event.add('uid', uid)
        event.add('summary', self.title)
        event.add('description', desc)

        event.add('dtstamp', parse_date('today'))

        if 'event_begin' in self.attrs and self.attrs['event_begin']:
            event.add('dtstart', self.attrs['event_begin']._date)
        elif 'due_date' in self.attrs and self.attrs['due_date']:
            event.add('dtstart', self.attrs['due_date']._date)

        # recurring zettels should also have event_begin
        if 'recurring' in self.attrs and self.attrs['recurring']:
            rrule = self.attrs['recurring']

            if 'recurring_stop' in self.attrs and self.attrs['recurring_stop']:
                rrule += f';until={self.attrs["recurring_stop"].asRrule()}'

            event['rrule'] = parse_rrule(rrule)

        # Add duration.
        if 'duration' in self.attrs and self.attrs['duration']:
            event.add('duration', parse_duration(self.attrs['duration']))

        # Parse dtend
        if 'event_end' in self.attrs and self.attrs['event_end']:
            event.add('dtend', self.attrs['event_end']._date)

        return event

    @classmethod
    def createFromMd(cls, md):
        """ Create a new Zettel from markdown text.

        The text will be parsed to derive key-value zettels where the key
        is the heading and the value is the subsequent text.

        The title of the zettel is expected to be a markdown level-1 heading
        (# ) This is followed by the zettel's _notes, which is then
        succeeded by the rest of the zettel's headings, which are expected
        to be RST level 2 headings (## ).

        Args:
            md: Markdown text or filename from which to create the zettel.

        Returns:
            A new Zettel.

        Raises:
            ValueError if the markdown could not create a valid Zettel.
        """
        if os.path.exists(md):
            with open(md) as f:
                md = f.read()

        md = md.strip()
        if not md:
            return Zettel('', {}, {})

        attr_header = '<!--- attributes --->'
        md = md.split(attr_header)
        if len(md) == 1:
            md.append('')

        # split out attributes and actual zettel text
        attributes = yaml.safe_load(md[-1].strip())
        md = attr_header.join(md[:-1]).splitlines()

        # Scrape the title
        title = ''
        if md and md[0].strip().startswith('# '):
            title = ' '.join(md[0].split()[1:])
            md = md[1:]

        # Find the content under title and headings.
        heading_pts = [x for x, y in enumerate(md) if _is_md_heading(y)] + [len(md)]

        headings = {}
        headings['_notes'] = '\n'.join(md[:heading_pts[0]])
        if not headings['_notes']:
            del(headings['_notes'])

        for ptr in range(len(heading_pts) - 1):
            heading = ''.join(md[heading_pts[ptr]].split('## ')[1:]).strip()
            content_start = heading_pts[ptr] + 1
            content_end = heading_pts[ptr + 1]
            headings[heading] = '\n'.join(md[content_start:content_end])

        return Zettel(title, headings, attributes)

    @classmethod
    def createFromRst(cls, rst):
        """ Create a new Zettel from RST text

        The title is expected to be an RST level-1 heading (=====). This
        is followed by the zettel's description.

        At the end of the description are the attributes. These are single
        line attributes which contain metadata about the zettel.

            ============================
             PROJ-77: My zettel's title
            ============================
            My zettels's description

            Other heading
            =============
            My other heading description

            .. attributes
            creator: OneRedDime
            assignee: OneRedDime
            creation_date: 03/01/2023

        Args:
            rst: RST-formatted text from which to create the zettel. This value
                be provided as a string of RST formatted text or a filename.

        Returns:
            A new Zettel.

        Raises:
            ValueError: If the RST could not create a valid Zettel.
        """
        if os.path.exists(rst):
            with open(rst) as f:
                rst = f.read()

        rst = rst.strip()
        if not rst:
            return Zettel('', {}, {})

        # Split out the attributes and content.
        attr_header = '.. attributes\n::'
        rst = rst.split(attr_header)
        if len(rst) == 1:
            rst.append('')

        attributes = yaml.safe_load(rst[-1].strip())
        rst = attr_header.join(rst[:-1]).splitlines()

        # Strip the first line of === if it exists.
        title = ''
        if len(rst) >= 3 and _is_rst_heading(rst[0]) and _is_rst_heading(rst[2]):
            title = rst[1].strip()
            rst = rst[3:]

        # Find the lines in the text that are heading markers.
        heading_pts = [x - 1 for x, y in enumerate(rst) if _is_rst_heading(y)] + [len(rst)]

        # Gather content under title
        headings = {}
        headings['_notes'] = '\n'.join(rst[:heading_pts[0]])
        if not headings['_notes']:
            del(headings['_notes'])

        # Get the rest
        for ptr in range(len(heading_pts) - 1):
            heading = rst[heading_pts[ptr]]
            content_start = heading_pts[ptr] + 2
            content_end = heading_pts[ptr + 1]
            headings[heading] = '\n'.join(rst[content_start:content_end])

        return Zettel(title, headings, attributes)

    def update(self, new_zettel, exp_headings=None):
        """ Update a zettel.

        The title, headings, and attributes of this zettel will be
        replaced with the ones in new_zettel.

        If exp_headings=None, then it would be as if the whole body text
        is replaced.

        But if exp_headings is provided, then only those headings will be
        be expected to be in the new zettel. If one of those is missing
        then it will be deleted while others will be ignored.

        Args:
            new_zettel: Other zettel instance whose attributes will be used.
            exp_headings: If a heading is listed here, but is not found in
                the final text, then the heading will be deleted.
        """
        exp_headings = exp_headings or []

        # Update this zettel.
        self.title = new_zettel.title

        orig_creation_date = self.attrs['creation_date']

        self.attrs = Attributes()
        self.attrs.update(new_zettel.attrs)
        self.attrs['creation_date'] = orig_creation_date

        if not exp_headings:
            self.headings = new_zettel.headings
        else:
            for heading in exp_headings:
                if heading not in new_zettel.headings and heading in self.headings:
                    del(self.headings[heading])

            self.headings.update(new_zettel.headings)

    def getMd(self, headings=None):
        """ Display this zettel in MD format.

        Args:
            headings: Only display these headings. The whole text will
                be displayed if not provided.

        Returns:
            A markdown string representing the content of this zettel.
        """
        headings = headings or []
        headings = headings or self.headings
        headings = [x.lower() for x in headings]

        s = []
        if self.title:
            s.append('# ' + self.title)

        if '_notes' in headings and self.headings['_notes']:
            s.append(self.headings['_notes'])

        # case-insensitive search
        lookup_headings = {k.lower(): k for k in self.headings}
        for heading in headings:
            if heading == '_notes' or heading not in lookup_headings:
                continue

            s.append('## ' + lookup_headings[heading])
            s.append(self.headings[lookup_headings[heading]])

        # Append the attributes
        s.append('<!--- attributes --->')
        s += ['    ' + x for x in str(self.attrs).splitlines()]
        s.append('')

        return '\n'.join(s)

    def getRst(self, headings=None):
        """ Display this zettel in RST format.

        Args:
            headings: Only display these headings. The whole text will
                be displayed if not provided.

        Returns:
            An RST string representing the content of this zettel.
        """

        headings = headings or []
        headings = headings or self.headings
        headings = [x.lower() for x in headings]

        s = []
        if self.title:
            s.append('=' * (len(self.title) + 2))
            s.append(' ' + self.title)
            s.append('=' * (len(self.title) + 2))

        if '_notes' in headings:
            s.append(self.headings['_notes'])

        # case-insensitive search
        lookup_headings = {k.lower(): k for k in self.headings}
        for heading in headings:
            if heading == '_notes' or heading not in lookup_headings:
                continue

            s.append(lookup_headings[heading])
            s.append('=' * len(lookup_headings[heading]))
            s.append(self.headings[lookup_headings[heading]])

        # Append the attributes
        s.append('.. attributes')
        s.append('::')
        s.append('')
        s += ['    ' + x for x in str(self.attrs).splitlines()]

        # Will become trailing newline
        s.append('')

        return '\n'.join(s)
