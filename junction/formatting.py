from string import whitespace
from functools import reduce


class LazyLookup:
    __slots__ = ['attr_name']

    def __init__(self, attr_name):
        self.attr_name = attr_name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.attr_name == other.attr_name
        else:
            return False

    def __len__(self):
        # Terminal escape sequences and the like have no visible length
        return 0

    def __bool__(self):
        return True

    def __iter__(self):
        return iter([self])

    def __str__(self):
        return ''

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__, self.attr_name)

    def do_lookup(self, obj):
        return getattr(obj, self.attr_name)


class Format(LazyLookup):
    '''A replacement for blessings.Terminal formatting strings that we can use
    to delay the determination of escape sequences until we're
    actually drawing an element. We're also used to produce smart
    StringWithFormatting objects that can be processed like strings without
    terminal escape sequences in them for the purposes of layout generation
    (i.e. using slices), but will preserve formatting.
    '''
    def __call__(self, content_string):
        return self + content_string + self.__class__('normal')

    def __add__(self, other):
        if isinstance(other, StringWithFormatting):
            return other.__radd__(self)
        else:
            return StringWithFormatting((self, other))

    def __radd__(self, other):
        return StringWithFormatting((other, self))

    def split(self, *args):
        return [self]

    def draw(self, terminal, default_format=None):
        if default_format and self.attr_name == 'normal':
            return default_format.draw(terminal)
        else:
            formatting_string = self.do_lookup(terminal)
            # FIXME: I'm not sure this is necessary:
            if default_format:
                formatting_string._normal = default_format.draw(terminal)
            return formatting_string


class ParameterizingFormat(Format):
    '''A special type of Format object that handles being called just like a
    blessings ParametrizingString.
    '''
    __slots__ = Format.__slots__ + ['args']

    def __init__(self, attr_name):
        super().__init__(attr_name)
        self.args = None

    def __repr__(self):
        if self.args:
            return '{}({}({}))'.format(
                self.__class__.__name__, self.attr_name,
                ', '.join(repr(arg) for arg in self.args))
        else:
            return super().__repr__()

    def __eq__(self, other):
        if super().__eq__(other):
            return self.args == other.args
        else:
            return False

    def __call__(self, *args):
        self.args = args
        return self

    def draw(self, terminal, default_format=None):
        parameterizing_string = super().draw(terminal, default_format)
        if self.args:
            return parameterizing_string(*self.args)
        else:
            return parameterizing_string


class FormatFactory:
    '''A simple helper object for constructing Format objects conveniently from
    Root in a similar way to format escape sequences being accessible from a
    blessings Terminal.
    '''
    __slots__ = []  # Ensure noone can store arbitrary attributes on us

    def __getattr__(self, attr_name):
        return self.get_format(attr_name)

    def get_format(self, attr_name):
        if attr_name in ('color', 'on_color'):
            return ParameterizingFormat(attr_name)
        else:
            return Format(attr_name)


class StringWithFormatting:
    __slots__ = ['_content']

    def __init__(self, content):
        if isinstance(content, self.__class__):
            self._content = content._content
        elif isinstance(content, str):
            self._content = tuple([content])
        else:
            self._content = tuple(content)

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__, ', '.join(repr(s) for s in self._content))

    def __str__(self):
        return ''.join(s for s in self._content if not isinstance(s, Format))

    def __len__(self):
        return len(str(self))

    def __bool__(self):
        # We're not False, even if we only have content that isn't printable
        return bool(self._content)

    def __contains__(self, obj):
        if isinstance(obj, Format):
            return obj in self._content
        else:
            return obj in str(self)

    def __eq__(self, other):
        if hasattr(other, '_content'):
            return self._content == other._content
        else:
            return False

    def __add__(self, other):
        if isinstance(other, Format):
            new_content = self._content + (other,)
        elif isinstance(other, str):
            if isinstance(self._content[-1], Format):
                new_content = self._content + (other,)
            else:
                # We want to keep runs of strings a long as possible, so make
                # something like ['hello'] + 'world' into ['helloworld'] not
                # ['hello', 'world']:
                new_content = self._content[:-1] + (self._content[-1] + other,)
        else:
            if not isinstance(self._content[-1], Format) and not isinstance(
                    other._content[-1], Format):
                # Similarly, we want to concat strings at each end of content
                # when adding two StringWithFormatting objects:
                new_content = (
                    self._content[:-1] +
                    (self._content[-1] + other._content[0],) +
                    other._content[1:])
            else:
                new_content = self._content + other._content
        return self.__class__(new_content)

    def __radd__(self, other):
        if isinstance(other, Format):
            new_content = (other,) + self._content
        else:
            if isinstance(self._content[0], Format):
                new_content = (other,) + self._content
            else:
                # Again, make longer runs of strings:
                new_content = (other + self._content[0],) + self._content[1:]
        return self.__class__(new_content)

    def __iter__(self):
        for string in self._content:
            for char in string:
                yield char

    def _enumerate_chars(self):
        num_chars = 0
        for char in self:
            num_chars += len(char)
            yield num_chars, char

    def _get_slice(self, start, stop):
        start = start if start is not None else 0
        stop = stop if stop is not None else len(self)
        stop = min(stop, len(self))
        result = []
        string = ''
        first_format = []
        for i, char in self._enumerate_chars():
            if start < i <= stop:
                if isinstance(char, Format):
                    if string:
                        result.append(string)
                        string = ''
                    result.append(char)
                else:
                    string += char
            else:
                if isinstance(char, Format):
                    first_format.append(char)
            if i == stop:
                if first_format:
                    result[0:0] = first_format
                if string:
                    result.append(string)
                break
        return self.__class__(result)

    def split(self, sep=None, maxsplit=-1):
        result = []
        for section in self._content:
            result.extend(section.split(sep))
        return result

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._get_slice(index.start, index.stop)
        else:
            return str(self)[index]

    def _iter_for_draw(self, terminal, default_format):
        for string in self._content:
            if isinstance(string, Format):
                yield string.draw(terminal, default_format)
            else:
                yield string

    def draw(self, terminal, default_format=None):
        return ''.join(
            string for string in self._iter_for_draw(terminal, default_format))


class TextWrapper:
    def __init__(self, width):
        self.width = width

    def _chunk(self, string_like):
        '''Generator that splits a string-like object (which can include our
        StringWithFormatting) into chunks at whitespace boundaries.
        '''
        current_chunk = ''  # Default if we have no characters
        previous_char_type = None
        for char in string_like:
            if isinstance(char, Format):
                char_type = 'format'
            elif char in whitespace:
                char_type = 'break'
            else:
                char_type = 'char'
            if char_type != previous_char_type:
                if current_chunk:
                    yield current_chunk
                current_chunk = char
            else:
                # FIXME: this currently won't work with consecutive Formats...
                current_chunk += char
            previous_char_type = char_type
        yield current_chunk

    def _lstrip(self, chunks):
        self._do_strip(chunks, range(len(chunks)))

    def _rstrip(self, chunks):
        self._do_strip(chunks, reversed(range(len(chunks))))

    def _do_strip(self, chunks, iter_):
        del_chunks = []
        for i in iter_:
            chunk = chunks[i]
            if not isinstance(chunk, Format):
                if chunk.strip() == '':
                    del_chunks.append(i)
                else:
                    break
        for i in reversed(sorted(del_chunks)):
            del chunks[i]

    def wrap(self, text):
        '''Wraps the text object to width, breaking at whitespaces. Runs of
        whitespace characters are preserved, provided they do not fall at a
        line boundary. The implementation is based on that of textwrap from the
        standard library, but we can cope with StringWithFormatting objects.

        :returns: a list of string-like objects.
        '''
        result = []
        chunks = list(self._chunk(text))
        while chunks:
            self._lstrip(chunks)
            current_line = []
            current_line_length = 0
            current_chunk_length = 0
            while chunks:
                current_chunk_length = len(chunks[0])
                if current_line_length + current_chunk_length <= self.width:
                    current_line.append(chunks.pop(0))
                    current_line_length += current_chunk_length
                else:
                    # Line is full
                    break
            # Handle case where chunk is bigger than an entire line
            if current_chunk_length > self.width:
                space_left = self.width - current_line_length
                current_line.append(chunks[0][:space_left])
                chunks[0] = chunks[0][space_left:]
            self._rstrip(current_line)
            if current_line:
                result.append(reduce(
                    lambda x, y: x + y, current_line[1:], current_line[0]))
            else:
                result.append('')
        return result


def wrap(text, width):
    w = TextWrapper(width)
    return w.wrap(text)
