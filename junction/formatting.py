from blessings import ParametrizingString


class Format:
    '''A wrapper for blessings.Terminal formatting commands that will delay the
    call to retrieve formatting until we're actually drawing an element. This
    means that parent elements could change style properties such as normal and
    we stay up-to-date.
    '''
    def __init__(self, escape_sequence, name=None):
        '''
        :parameter escape_sequence: the text-formatting terminal escape
            sequence this Format object is to encapsulate, or None if this
            object is to act like the 'normal' format, but where 'normal' could
            potentially be another format defined arbitrarily.
        '''
        self.escape_sequence = escape_sequence
        self.name = name

    def __str__(self):
        return self.escape_sequence

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__, self.name or repr(self.escape_sequence))

    def __call__(self, *args):
        if isinstance(self.escape_sequence, ParametrizingString):
            return self.__class__(self.escape_sequence(*args), name=self.name)
        else:
            # Emulate the behaviour of blessings.FormattingString, but with our
            # StringWithFormatting objects instead
            result = self
            for word in args:
                result += word
            result += Format(None)
            return result

    def __eq__(self, other):
        if hasattr(other, 'escape_sequence'):
            return self.escape_sequence == other.escape_sequence
        else:
            return False

    def __add__(self, other):
        if isinstance(other, StringWithFormatting):
            return other.__radd__(self)
        else:
            return StringWithFormatting((self, other))

    def __radd__(self, other):
        return StringWithFormatting((other, self))

    def draw(self, normal):
        return self.escape_sequence or normal


class StringWithFormatting:
    def __init__(self, content):
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
            return self.__class(self._content + other._content)

    def __radd__(self, other):
        if isinstance(other, (str, Format)):
            return self.__class__((other,) + self._content)
        else:
            return self.__class__(other._content + self._content)

    def _enumerate_chars(self):
        num_chars = 0
        for string in self._content:
            if isinstance(string, Format):
                yield num_chars, string
            else:
                for char in string:
                    num_chars += 1
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
