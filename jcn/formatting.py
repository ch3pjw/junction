# Copyright (C) 2013 Paul Weaver <p.weaver@ruthorn.co.uk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].

from functools import wraps
from itertools import islice

from .terminal import get_terminal
from .util import InheritDocstrings


class EscapeSequenceStack:
    '''An :class:`EscapeSequenceStack` is used to keep track of what formatting
    escape sequences have been applied by a :class:`StringWithFormatting`
    during the drawing process, so that we can step back and 'undo' the last
    one when we need to go back to a previous set of formatting options.
    '''
    def __init__(self, default_escape_sequence):
        '''
        :parameter str default_escape_sequence: The escape sequence used by
            this stack as the 'reset' command for the terminal. (Will almost
            certainly be :attr:`jcn.Terminal.normal`.)
        '''
        self.default_escape_sequence = default_escape_sequence
        self._stack = []

    def push(self, esc_seq):
        '''Push a new escapse sequence onto the stack.

        :parameter str esc_seq: The terminal escape sequence to push onto the
            stack.
        '''
        self._stack.append(esc_seq)

    def pop(self):
        '''Pops the last escape sequence from the stack *and returns a string
        containing all the remaining escape sequences that should be in effect
        on the terminal*.

        .. note::
            This method may be named poorly, suggestions for improving it would
            be welcome.

        :returns str: Returns a string of the escape sequences remaining in the
            stack, so as effectively to 'undo' the one that has just been
            popped off.
        '''
        self._stack.pop()
        return self.default_escape_sequence + ''.join(self._stack)


class Placeholder(metaclass=InheritDocstrings):
    '''Placeholders are objects that will provide concrete terminal escape
    sequences dynamically. At creation time they are merely
    given a name as a reference to use at draw-time, when their
    :meth:`Placeholder.populate` method will be called with current
    escape-sequence-providing objects. These objects are also provided by the
    :attr:`Root.format` and :attr:`Root.style` factories as the entry point to
    their formatting and style definition.
    '''
    __slots__ = ['attr_name']

    def __init__(self, attr_name):
        '''
        :parameter str attr_name: The name of the attribute/entry this object
            references. This will only be resolved at draw time, so, in the
            case of styles, the style need not yet be defined to be referenced
            by a :class:`Placeholder`.
        '''
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
            raise TypeError(
                "Can't add object of type {} to {!r} - to construct content "
                "using formatting placeholders, please call the placeholder "
                "with the content you desire to be formatted".format(
                    type(other), self))

    def __call__(self, content):
        '''Designate the given content to be formatted according to the
        formatting referenced by this :class:`Placeholder`.

        :parameter content: The content the Junction is to format with this
            object's formatting.
        :type content: :class:`str`, :class:`StringComponentSpec` or
            :class:`StringWithFormatting`
        :returns: A :class:`StringComponentSpec` object referencing both the
            given content and this :class:`Placeholder` instance.
        '''
        return StringComponentSpec(self, content)

    def populate(self, terminal, styles):
        '''
        :parameter Terminal terminal: A :class:`jcn.Terminal` object from which
            to retrieve format escape sequences by attribute lookup.
        :parameter StylePlacholderFactory styles: A
            :class:`StylePlaceholderFactory` object from which to look up
            other :class:`Placeholder` objects by name. These referenced
            :class:`Placeholder` objects represent a semantically meaningful
            set of formatting and can be recursively resolved to concrete
            escape sequences.
        '''
        raise NotImplementedError()


class FormatPlaceholder(Placeholder):
    '''A :class:`FormatPlaceholder` references :class:`jcn.Terminal` escape
    sequence attributes such as 'red', 'bold' or 'underline'.
    '''
    def populate(self, terminal, styles):
        return getattr(terminal, self.attr_name)


class ParameterizingFormatPlaceholder(FormatPlaceholder):
    '''A :class:`ParameterizingFormatPlaceholder` object references
    :class:`jcn.Terminal` escape sequence attributes that are callable and take
    parameters, such as 'color'.
    '''
    __slots__ = Placeholder.__slots__ + ['args']

    def __init__(self, attr_name):
        super().__init__(attr_name)
        self.args = None

    def __eq__(self, other):
        if super().__eq__(other):
            return self.args == other.args
        else:
            return False

    def _protect_from_not_called(self):
        if not self.args:
            raise ValueError(
                "FIXME: improve message. You can't use me anywhere yet, "
                "because I don't refer to any concrete information.")

    def __add__(self, other):
        self._protect_from_not_called()
        return super().__add__(other)

    def __call__(self, *args):
        '''FIXME:
        '''
        if not self.args:
            self.args = args
            return self
        else:
            return super().__call__(*args)

    def populate(self, terminal, styles):
        self._protect_from_not_called()
        return super().populate(terminal, styles)(*self.args)


class StylePlaceholder(Placeholder):
    '''FIXME:
    '''
    def populate(self, terminal, styles):
        style = styles[self.attr_name]
        return style.populate(terminal, styles)


class PlaceholderGroup:
    '''FIXME:
    Note why we don't have a __call__ method
    '''
    def __init__(self, placeholders=None):
        if isinstance(placeholders, self.__class__):
            placeholders = placeholders.placeholders
        self.placeholders = tuple(placeholders) if placeholders else tuple()

    def __repr__(self):
        return '{}([{}])'.format(
            self.__class__.__name__,
            ', '.join(repr(p) for p in self.placeholders))

    def __add__(self, other):
        if isinstance(other, Placeholder):
            return self.__class__(self.placeholders + (other,))
        elif isinstance(other, PlaceholderGroup):
            return self.__class__(self.placeholders + other.placeholders)
        else:
            raise TypeError('FIXME: add message')

    def populate(self, terminal, styles):
        escape_sequence = ''
        for placeholder in self.placeholders:
            string = placeholder.populate(terminal, styles)
            escape_sequence += string
        return escape_sequence
    populate.__doc__ = Placeholder.populate.__doc__


class FormatPlaceholderFactory:
    '''FIXME: document this
    '''
    __slots__ = []  # Ensure noone can store arbitrary attributes on us

    def __getattr__(self, attr_name):
        '''FIXME:
        '''
        if attr_name == '__isabstractmethod__':
            return False
        else:
            if attr_name in ('color', 'on_color'):
                return ParameterizingFormatPlaceholder(attr_name)
            else:
                return FormatPlaceholder(attr_name)


class StylePlaceholderFactory:
    '''FIXME: document this
    '''
    __slots__ = ['_defined_styles']

    def __init__(self):
        super().__setattr__('_defined_styles', {})

    def __getattr__(self, name):
        '''FIXME:
        '''
        if name == '__isabstractmethod__':
            return False
        else:
            return StylePlaceholder(name)

    def __setattr__(self, name, value):
        '''FIXME:
        '''
        if value is None:
            del self._defined_styles[name]
        else:
            self._defined_styles[name] = value

    def __getitem__(self, name):
        '''FIXME:
        '''
        return self._defined_styles[name]


class StringComponentSpec:
    '''A string component specification is an object that will be used to form
    part of a string-like object that contains formatting information as well
    as printable characters.
    '''
    __slots__ = ['placeholder', 'content', '_str']

    def __init__(self, placeholder, content):
        '''FIXME:
        '''
        self.placeholder = placeholder
        self.content = content
        self._str = None

    def __repr__(self):
        return '{}({!r}, {!r})'.format(
            self.__class__.__name__, self.placeholder, self.content)

    def __str__(self):
        if self._str is None:
            # We're supposed to be immutable, and calculating our str is
            # potentially quite expensive, so cache the result:
            self._str = str(self.content)
        return self._str

    def __getattr__(self, attr_name):
        '''FIXME:
        '''
        str_method = getattr(self.content, attr_name)
        @wraps(str_method)
        def do_str_method(*args, **kwargs):
            result = str_method(*args, **kwargs)
            if isinstance(result, str):
                return self.__class__(self.placeholder, result)
            elif isinstance(result, list):
                return [self.__class__(self.placeholder, s) for s in result]
            else:
                return result
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
        '''FIXME:
        '''
        return self.__class__(self.placeholder, self.content[index])

    def _sanitise_other(self, other):
        if isinstance(other, str):
            return NullComponentSpec(other)
        elif isinstance(other, StringComponentSpec):
            return other
        else:
            raise TypeError('Cannot add object with type {} to {!r}'.format(
                type(other), self))

    def __add__(self, other):
        other = self._sanitise_other(other)
        result = StringWithFormatting((self, other))
        return result

    def __radd__(self, other):
        other = self._sanitise_other(other)
        return StringWithFormatting((other, self))

    def chunk(self, regex):
        '''FIXME:
        '''
        if hasattr(self.content, 'chunk'):
            chunks = self.content.chunk(regex)
        else:
            chunks = regex.split(self.content)
        chunks = [self.__class__(self.placeholder, c) for c in chunks if c]
        return chunks

    def populate(self, terminal=None, styles=None, esc_seq_stack=None):
        '''Get the concrete (including terminal escape sequences)
        representation of this string.

        :parameter Terminal terminal: The terminal object to use for turning
            formatting attributes such as :attr:`Root.format.blue` into
            concrete escape sequences.
        :parameter styles: An object from which to look up style definitions,
            which ultimately resolve to escape sequences, but may resolve to
            other intermediaries, including other styles.
        :type styles: StylePlaceholderFactory or dict
        :parameter EscapeSequenceStack esc_seq_stack: An
            :class:`EscapeSequenceStack` for tracking which styles have been
            applied to the given terminal, so that during the drawing process
            we can 'undo' the last format that we applied to the terminal.
        :returns str: Returns a concrete string, containing all the escape
            sequences required to render the string to the terminal with the
            desired formatting.

        .. note::
            All parameters are optional, and will be populated with sensible
            defaults if ommitted. This is to assist testing and experimentation
            with lower-level parts of Junction. If you want to use a
            :class:`StringWithFormatting` object as part of a wider
            application, it is suggested that you always pass all the arguments
            explicitly.
        '''
        terminal = terminal or get_terminal()
        styles = styles or {}
        esc_seq_stack = esc_seq_stack or EscapeSequenceStack(terminal.normal)
        esc_seq = self.placeholder.populate(terminal, styles)
        esc_seq_stack.push(esc_seq)
        if hasattr(self.content, 'populate'):
            content = self.content.populate(
                terminal, styles, esc_seq_stack)
        else:
            content = self.content
        return esc_seq + content + esc_seq_stack.pop()


class NullComponentSpec(StringComponentSpec):
    '''FIXME:
    '''
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


class StringComponent(str):
    _method_cache = {}

    def __new__(cls, placeholder, string, *args, **kwargs):
        obj = super().__new__(cls, string, *args, **kwargs)
        obj.placeholder = placeholder
        return obj

    def __repr__(self):
        return '{}({!r}, {})'.format(
            self.__class__.__name__, self.placeholder, super().__repr__())

    def __eq__(self, other):
        if super().__eq__(other):
            if hasattr(other, 'placeholder'):
                return other.placeholder == self.placeholder
            else:
                return self.placeholder is None
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getattribute__(self, name):
        try:
            return super().__getattribute__('_method_cache')[name]
        except KeyError:
            attr = super().__getattribute__(name)
            if callable(attr) and not name.startswith('__'):
                @wraps(attr)
                def wrapped_str_method(*args, **kwargs):
                    result = attr(*args, **kwargs)
                    if isinstance(result, list):
                        result = [
                            self.__class__(self.placeholder, s) for s in
                            result]
                    elif isinstance(result, str):
                        result = self.__class__(self.placeholder, result)
                    return result
                self._method_cache[name] = wrapped_str_method
                return wrapped_str_method
            else:
                return attr


class StringWithFormatting:
    '''FIXME:
    '''
    __slots__ = ['_content', '_str']

    def __init__(self, content):
        '''FIXME:
        :attr:`_content` is a tuple of (:class:`Placholder`, strings)
        '''
        if isinstance(content, self.__class__):
            self._content = content._content
        elif isinstance(content, StringComponent):
            self._content = (content,)
        elif isinstance(content, str):
            self._content = (StringComponent(None, content),)
        else:
            self._content = content
        self._str = None  # FIXME: needed?

    def __repr__(self):
        return '{}({!r})'.format(
            self.__class__.__name__, self._content)

    def __str__(self):
        return ''.join(self._content)

    def __len__(self):
        return sum(len(s.string) for s in self._content)

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
            return (None, (other,))
        elif hasattr(other, '_content'):
            return other._content
        else:
            raise TypeError('FIXME: message')

    def __add__(self, other):
        new_content = self._get_new_content(other)
        return self.__class__(self._content + new_content)

    def __radd__(self, other):
        new_content = self._get_new_content(other)
        return self.__class__(new_content + self._content)

    def __iter__(self):
        for placeholder, string in self._content:
            for char in string:
                yield char

    def _get_slice(self, start, stop):
        #FIXME: this is going to be broken, again, probably
        slice_start = start if start is not None else 0
        slice_stop = stop if stop is not None else len(self)
        slice_stop = min(slice_stop, len(self))
        result = []
        sec_start = 0
        for placeholder, strings in self._content:
            new_strings = []
            for string in strings:
                str_stop = str_start + len(string)
                if str_start >= slice_start and str_stop <= slice_stop:
                    section.append(section)
                elif str_start < slice_start < str_stop:
                    section.append(string[
                        slice_start - str_start:slice_stop - str_start])
                elif str_start < slice_stop <= str_stop:
                    section.append(string[:slice_stop - str_start])
                str_start = str_stop
            result.append(placeholder, tuple(new_strings))
            if str_stop >= slice_stop:
                break
        return self.__class__(tuple(result))

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._get_slice(index.start, index.stop)
        else:
            return str(self)[index]

    def __getattr__(self, name):
        '''We attemt to provide access to all methods that are available on a
        regular str object, whilst wrapping up answers appropriately.
        '''
        # FIXME: definitely broken
        str_cls_method = getattr(str, name)
        @wraps(str_cls_method)
        def str_method_executor(*args, **kwargs):
            reference = str_cls_method(str(self), *args, **kwargs)
            if isinstance(reference, list):
                return self._apply_str_method(
                    name, *args, reference=reference, **kwargs)
            elif isinstance(reference, str):
                raise NotImplementedError(
                    "str method {!r} has not yet been implemented for a {}, "
                    "sorry :-(".format(name, self.__class__.__name__))
            else:
                return reference
        return str_method_executor

    def chunk(self, regex):
        '''FIXME:
        '''
        chunks = []
        for component in self._content:
            chunks.extend(
                StringComponent(component.placeholder, s) for s in
                regex.split(str(component)))
        for i, (chunk1, chunk2) in enumerate(
                zip(chunks, islice(chunks, 1, None))):
            if chunk1.placeholder is not chunk2.placeholder:
                # We're crossing a boundary between placeholders
                if chunk1.strip() and chunk2.strip():
                    # There's no whitespace at the boundary, so stick the
                    # chunks together
                    chunks[i:i + 2] = [self.__class__((chunk1, chunk2))]
                else:
                    chunks[i] = self.__class__((chunk1,))
            else:
                chunks[i] = self.__class__((chunk1,))
        chunks[-1] = self.__class__((chunk2,))
        return chunks

    def strip(self):
        '''FIXME:
        '''
        if len(self._content) == 0:
            return self
        elif len(self._content) == 1:
            return self.__class__(self._content[0].strip())
        else:
            first = self._content[0].lstrip()
            last = self._content[-1].rstrip()
            total = (first,) + self._content[1:-1] + (last,)
            return self.__class__(total)

    def populate(self, terminal=None, styles=None, esc_seq_stack=None):
        terminal = terminal or get_terminal()
        styles = styles or {}
        esc_seq_stack = esc_seq_stack or EscapeSequenceStack(terminal.normal)
        return ''.join(
            s.populate(terminal, styles, esc_seq_stack) for s in self._content)
    #FIXME: populate.__doc__ = StringComponentSpec.populate.__doc__
