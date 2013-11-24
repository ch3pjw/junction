from blessings import ParametrizingString
from string import whitespace
from functools import reduce


class Format(str):
    '''A replacement for blessings.Terminal formatting strings that we can use
    to delay the determination of what 'normal' formatting is until we're
    actually drawing an element. We're also used to produce smart
    StringWithFormatting objects that can be processed like strings without
    terminal escape sequences in them for the purposes of layout generation
    (i.e. using slices), but will preserve formatting.
    '''
    __slots__ = ('_normal', '_orig_class', 'name')

    def __new__(cls, escape_sequence, name=None):
        '''
        :parameter escape_sequence: the text-formatting terminal escape
            sequence this Format object is to embody, or None if this
            object is to act like the 'normal' format, but where 'normal' could
            potentially be another format defined arbitrarily.
        '''
        if escape_sequence is None:
            # Whether this format is representing 'normal' formatting. We
            # provide this also to maintain compatibility with
            # blessings.ParametrizingString:
            _normal = True
            escape_sequence = ''
        else:
            _normal = False
        obj = super().__new__(cls, escape_sequence)
        obj._orig_class = escape_sequence.__class__
        obj._normal = _normal
        obj.name = name
        return obj

    def __len__(self):
        # Terminal escape sequences have no visible length
        return 0

    def __bool__(self):
        return True

    def __iter__(self):
        return iter([self])

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__, self.name or super().__repr__())

    def __call__(self, *args):
        if issubclass(self._orig_class, ParametrizingString):
            return self.__class__(
                self._orig_class.__call__(self, *args),
                name=self.name)
        else:
            # Emulate the behaviour of blessings.FormattingString, but with our
            # StringWithFormatting objects instead
            result = self
            for word in args:
                result += word
            result += Format(None)
            return result

    def __add__(self, other):
        if isinstance(other, StringWithFormatting):
            return other.__radd__(self)
        else:
            return StringWithFormatting((self, other))

    def __radd__(self, other):
        return StringWithFormatting((other, self))

    def draw(self, normal):
        if self._normal:
            return normal
        else:
            return self

    def split(self, *args):
        return [self]


class StringWithFormatting:
    __slots__ = ['_content']

    def __init__(self, content):
        if isinstance(content, self.__class__):
            self._content = content._content
        else:
            self._content = tuple(content)

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__, ', '.join(repr(s) for s in self._content))

    def __str__(self):
        return ''.join(s for s in self._content if not isinstance(s, Format))

    def __len__(self):
        return len(str(self))

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
        if isinstance(other, (str, Format)):
            return self.__class__(self._content + (other,))
        else:
            return self.__class__(self._content + other._content)

    def __radd__(self, other):
        if isinstance(other, (str, Format)):
            return self.__class__((other,) + self._content)

    def _enumerate_chars(self):
        num_chars = 0
        for string in self._content:
            for char in string:
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

    def wrap(self, width):
        '''Wraps the string at whitepaces, preserving runs of whitespace
        characters provided they do not fall at a line boundary. The
        implementation is based on that of textwrap from the standard library.
        '''
        result = []
        chunks = list(self._chunk())
        while chunks:
            self._lstrip(chunks)
            current_line = []
            current_length = 0
            while chunks:
                l = len(chunks[0])
                if current_length + l <= width:
                    current_line.append(chunks.pop(0))
                    current_length += l
                else:
                    # Line is full
                    break
            # Handle case where chunk is bigger than an entire line
            if l > width:
                space_left = width - current_length
                current_line.append(chunks[0][:space_left])
                chunks[0] = chunks[0][space_left:]
            self._rstrip(current_line)
            result.append(reduce(lambda x, y: x + y, current_line, ''))
        return result

    def split(self, sep=None, maxsplit=-1):
        result = []
        for section in self._content:
            result.extend(section.split(sep))
        return result

    def _chunk(self):
        current_chunk = None
        previous_char_type = None
        for _, char in self._enumerate_chars():
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
                current_chunk += char
            previous_char_type = char_type
        yield current_chunk

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._get_slice(index.start, index.stop)
        else:
            return str(self)[index]

    def _iter_for_draw(self, normal):
        for string in self._content:
            if isinstance(string, Format):
                yield string.draw(normal)
            else:
                yield string

    def draw(self, normal):
        return ''.join(string for string in self._iter_for_draw(normal))
