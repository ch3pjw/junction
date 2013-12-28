from textwrap import TextWrapper as _TextWrapper
from functools import reduce, wraps


class EscapeSequenceStack:
    def __init__(self, esc_seq):
        self._stack = []
        if esc_seq:
            self.push(esc_seq)

    def push(self, esc_seq):
        self._stack.append(esc_seq)

    def pop(self):
        '''Pops the last escape sequence from the stack *and returns a string
        containing all the remaining escape sequences that should be in effect
        on the terminal*.
        '''
        self._stack.pop()
        return ''.join(self._stack)


class Placeholder:
    '''Placeholders represent objects that will at some point be transformed
    into terminal escape sequences.
    '''
    __slots__ = ['attr_name']

    def __init__(self, attr_name):
        self.attr_name = attr_name

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.attr_name)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.attr_name == other.attr_name
        else:
            return False

    def __add__(self, other):
        if isinstance(other, Placeholder):
            return PlaceholderGroup((self, other))
        else:
            raise TypeError('FIXME: add message')

    def populate(self, terminal, styles):
        raise NotImplementedError()


class FormatPlaceholder(Placeholder):
    def populate(self, terminal, styles):
        return getattr(terminal, self.attr_name)


class StylePlaceholder(Placeholder):
    def populate(self, terminal, styles):
        style = styles.get(self.attr_name)
        return style.populate(terminal, styles)


class PlaceholderGroup:
    def __init__(self, placeholders):
        if isinstance(placeholders, self.__class__):
            placeholders = placeholders.placeholders
        self.placeholders = list(placeholders)

    def __add__(self, other):
        if isinstance(other, Placeholder):
            self.placeholders.append(other)
        elif isinstance(other, PlaceholderGroup):
            self.placeholders.extend(other.placeholders)
        else:
            raise TypeError('FIXME: add message')

    def populate(self, terminal, styles):
        escape_sequence = ''
        for placeholder in self.placeholders:
            string = placeholder.populate(terminal, styles)
            escape_sequence += string
        return escape_sequence


class StringComponentSpec:
    '''A string component specification is an object that will be used to form
    part of a string-like object that contains formatting information as well
    as printable characters.
    '''
    __slots__ = ['placeholder', 'content']

    def __init__(self, placeholder, content=None):
        self.placeholder = placeholder
        self.content = content

    def __repr__(self):
        return '{}({!r}, {!r})'.format(
            self.__class__.__name__, self.placeholder, self.content)

    def __str__(self):
        return str(self.content)

    def __getattr__(self, attr_name):
        str_method = getattr(self.content, attr_name)
        @wraps(str_method)
        def do_str_method(*args, **kwargs):
            new_str = str_method(*args, **kwargs)
            return self.__class__(self.placeholder, new_str)
        return do_str_method

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.placeholder == other.placeholder and
                self.content == other.content)
        else:
            return False

    def __len__(self):
        return len(self.content)

    def __bool__(self):
        return True

    def __iter__(self):
        return iter(self.content)

    def __getitem__(self, index):
        return self.__class__(self.placeholder, self.content[index])

    def __call__(self, content):
        if self.content is None:
            self.content = content
            return self
        else:
            raise ValueError(
                '{!r} has already been called, and therefore already has '
                'existing content'.format(self))

    def _protect_early_addition(self):
        if self.content is None:
            raise ValueError(
                'Missing content for {}({!r}) - you tried to add styling data '
                'to an existing content object without first calling your '
                'style to specifiy the newly styled content'.format(
                    self.__class__.__name__, self.placeholder))

    def _sanitise_other(self, other):
        if isinstance(other, str):
            return NullComponentSpec(other)
        elif isinstance(other, StringComponentSpec):
            return other
        else:
            raise TypeError('Cannot add object with type {} to {!r}'.format(
                type(other), self))

    def __add__(self, other):
        self._protect_early_addition()
        other = self._sanitise_other(other)
        return StringWithFormatting((self, other))

    def __radd__(self, other):
        self._protect_early_addition()
        other = self._sanitise_other(other)
        return StringWithFormatting((other, self))

    def chunk(self, regex):
        if isinstance(self.content, StringComponentSpec):
            chunks = self.content.chunk(regex)
        else:
            chunks = regex.split(self.content)
        chunks = [self.__class__(self.placeholder, c) for c in chunks if c]
        return chunks

    def populate(self, terminal, styles, esc_seq_stack):
        esc_seq = self.placeholder.populate(terminal, styles)
        if self.content is None:
            # Someone might look us up as Root.format.blue, and want to use us
            # with no content as a definition of what blue is (i.e. just want
            # to refer to our placeholder directly)
            return esc_seq
        else:
            esc_seq_stack.push(esc_seq)
            if isinstance(self.content, StringComponentSpec):
                content = self.content.populate(
                    terminal, styles, esc_seq_stack)
            else:
                content = self.content
            return esc_seq + content + esc_seq_stack.pop()


class NullComponentSpec(StringComponentSpec):
    def __init__(self, *args):
        if len(args) == 1:
            super().__init__(placeholder=None, content=args[0])
        else:
            super().__init__(*args)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.content)

    def populate(self, *args, **kwargs):
        assert isinstance(self.content, str)
        return self.content


class ParameterizingSpec(StringComponentSpec):
    '''A special type of StringComponentSpec object that handles being called
    just like a blessings ParametrizingString.
    '''
    __slots__ = StringComponentSpec.__slots__ + ['args']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = None

    def __repr__(self):
        if self.args:
            return '{}({!r})({})'.format(
                self.__class__.__name__, self.placeholder,
                ', '.join(repr(arg) for arg in self.args))
        else:
            return super().__repr__()

    def __eq__(self, other):
        if super().__eq__(other):
            return self.args == other.args
        else:
            return False

    def __call__(self, *args):
        if self.args:
            return super().__call__(*args)
        else:
            self.args = args
            return self

    def populate(self, terminal):
        parameterizing_string = self.placeholder.populate(terminal, {})
        if self.args:
            return parameterizing_string(*self.args) + self.content
        else:
            raise ValueError(
                "{!r} has not been called with parameterizing argument(s), "
                "such as a numerical colour, so we can't go about drawing a "
                "concrete format to the screen!".format(self))


class FormatSpecFactory:
    '''FIXME: document this
    '''
    __slots__ = []  # Ensure noone can store arbitrary attributes on us

    def __getattr__(self, attr_name):
        if attr_name == '__isabstractmethod__':
            return False
        else:
            if attr_name in ('color', 'on_color'):
                return ParameterizingSpec(FormatPlaceholder(attr_name))
            else:
                return StringComponentSpec(FormatPlaceholder(attr_name))


class StyleSpecFactory:
    __slots__ = []  # Ensure noone can store arbitrary attributes on us

    def __getattr__(self, attr_name):
        if attr_name == '__isabstractmethod__':
            return False
        else:
            return StringComponentSpec(StylePlaceholder(attr_name))


class StringWithFormatting:
    __slots__ = ['_content']

    def __init__(self, content):
        if isinstance(content, self.__class__):
            self._content = content._content
        elif isinstance(content, StringComponentSpec):
            self._content = (content,)
        elif isinstance(content, str):
            self._content = (NullComponentSpec(content),)
        else:
            self._content = tuple()
            for string_spec in content:
                self._content = self._join_content(
                    self._content, (string_spec,))

    def __repr__(self):
        return '{}([{}])'.format(
            self.__class__.__name__, ', '.join(repr(s) for s in self._content))

    def __str__(self):
        return ''.join(map(str, self._content))

    def __len__(self):
        return len(str(self))

    def __bool__(self):
        # We're not False, even if we only have content that isn't printable
        return bool(self._content)

    def __contains__(self, string):
            return string in str(self)

    def __eq__(self, other):
        if hasattr(other, '_content'):
            return self._content == other._content
        else:
            return False

    def _get_new_content(self, other):
        if isinstance(other, str):
            new_content = (NullComponentSpec(other),)
        elif isinstance(other, StringComponentSpec):
            new_content = (other,)
        elif isinstance(other, StringWithFormatting):
            new_content = other._content
        else:
            raise TypeError('FIXME: nicer message!')
        return new_content

    def _join_content(self, content1, content2):
        '''Takes the contents of two StringWithFormatting objects and joins
        them together for making a new one, but taking care of the fact that if
        we have two string_spec objects of the same type at the join, we should
        glue them together.
        '''
        spec1 = content1[-1] if content1 else None
        spec2 = content2[0] if content2 else None
        if spec1 and type(spec1) is type(spec2):
            spec1.content = spec1.content + spec2.content
            content2 = content2[1:]
        return content1 + content2

    def __add__(self, other):
        new_content = self._get_new_content(other)
        content = self._join_content(self._content, new_content)
        return self.__class__(content)

    def __radd__(self, other):
        new_content = self._get_new_content(other)
        content = self._join_content(new_content, self._content)
        return self.__class__(content)

    def __iter__(self):
        for string in self._content:
            for char in string:
                yield char

    def _get_slice(self, start, stop):
        slice_start = start if start is not None else 0
        slice_stop = stop if stop is not None else len(self)
        slice_stop = min(slice_stop, len(self))
        result = []
        spec_start = 0
        for string_spec in self._content:
            spec_stop = spec_start + len(string_spec)
            if spec_start >= slice_start and spec_stop <= slice_stop:
                result.append(string_spec)
            elif spec_start < slice_start < spec_stop:
                result.append(string_spec[
                    slice_start - spec_start:slice_stop - spec_start])
            elif spec_start < slice_stop <= spec_stop:
                result.append(string_spec[:slice_stop - spec_start])
            if spec_stop >= slice_stop:
                break
            spec_start = spec_stop
        return self.__class__(result)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._get_slice(index.start, index.stop)
        else:
            return str(self)[index]

    def chunk(self, regex):
        chunked_specs = []
        for spec in self._content:
            chunks = spec.chunk(regex)
            chunks = [self.__class__(c) for c in chunks]
            chunked_specs.extend(chunks)
        # Because we started by iterating over the individual specs in our
        # content, we might have two 'chunks' in result that are actually part
        # of the same logical word, so we need to recombine them
        result = []
        iterator = iter(chunked_specs)
        prev_swf = iterator.__next__()  # Cheeky steal of the first one :-)
        for swf in iterator:
            if len(prev_swf.strip()) != 0 and len(swf.strip()) != 0:
                # Neither string is whitespace
                prev_swf = prev_swf + swf
                continue
            else:
                result.append(prev_swf)
                prev_swf = swf
        result.append(prev_swf)
        return result

    def strip(self):
        if len(self._content) == 0:
            return self.__class__(self)
        elif len(self._content) == 1:
            return self.__class__(self._content[0].strip())
        else:
            first = self._content[0].lstrip()
            last = self._content[-1].rstrip()
            total = (first,) + self._content[1:-1] + (last,)
            return self.__class__(total)

    def populate(self, terminal, styles=None, esc_seq_stack=None):
        # FIXME: esc_seq_stack should probably be mandatory
        return ''.join(
            s.populate(terminal, styles, esc_seq_stack) for s in self._content)


class TextWrapper:
    def __init__(self, width, break_on_hyphens=True):
        self.width = width
        self.break_on_hyphens = break_on_hyphens

    def _chunk(self, string_like):
        if self.break_on_hyphens:
            regex = _TextWrapper.wordsep_re
        else:
            regex = _TextWrapper.wordsep_simple_re

        if isinstance(string_like, StringWithFormatting):
            chunks = string_like.chunk(regex)
        else:
            chunks = regex.split(string_like)
            chunks = [c for c in chunks if c]

        return chunks

    def _lstrip(self, chunks):
        self._do_strip(chunks, range(len(chunks)))

    def _rstrip(self, chunks):
        self._do_strip(chunks, reversed(range(len(chunks))))

    def _do_strip(self, chunks, iter_):
        del_chunks = []
        for i in iter_:
            chunk = chunks[i]
            if str(chunk.strip()) == '':
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
        chunks = self._chunk(text)
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
