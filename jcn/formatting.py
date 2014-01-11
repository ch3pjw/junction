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

import types
from functools import wraps
from itertools import islice

from .terminal import get_terminal
from .util import InheritDocstrings


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
        if isinstance(content, StringComponent):
            return StringComponent(content.placeholder + self, content)
        elif isinstance(content, StringWithFormatting):
            return content.apply_placeholder(self)
        else:
            return StringComponent(self, content)

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

    def __repr__(self):
        r = super().__repr__()
        if self.args is not None:
            r += '({})'.format(', '.join(map(repr, self.args)))
        return r

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


class NullPlaceholder(Placeholder):
    def __init__(self):
        super().__init__('')

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def populate(self, terminal, styles):
        return ''

null_placeholder = NullPlaceholder()


class PlaceholderGroup:
    '''FIXME:
    '''
    def __init__(self, placeholders=None):
        if isinstance(placeholders, self.__class__):
            placeholders = placeholders.placeholders
        self.placeholders = tuple(placeholders) if placeholders else tuple()

    def __repr__(self):
        return '{}([{}])'.format(
            self.__class__.__name__,
            ', '.join(repr(p) for p in self.placeholders))

    def __eq__(self, other):
        if hasattr(other, 'placeholders'):
            return other.placeholders == self.placeholders
        else:
            return False

    def __add__(self, other):
        if isinstance(other, Placeholder):
            return self.__class__(self.placeholders + (other,))
        elif isinstance(other, PlaceholderGroup):
            return self.__class__(self.placeholders + other.placeholders)
        else:
            raise TypeError('FIXME: add message')

    def __call__(self, content):
        '''FIXME:
        '''
        return StringComponent(self, content)

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
                return self.placeholder is null_placeholder
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getitem__(self, index):
        return self.__class__(self.placeholder, super().__getitem__(index))

    def __add__(self, other):
        # FIXME: this is messy
        if hasattr(other, 'placeholder'):
            if other.placeholder is self.placeholder:
                return self.__class__(self.placeholder, str(self) + str(other))
        elif isinstance(other, StringWithFormatting):
            return other.__radd__(self)
        elif isinstance(other, str):
            if self.placeholder is null_placeholder:
                return self.__class__(null_placeholder, str(self) + other)
            else:
                other = self.__class__(null_placeholder, other)
        return StringWithFormatting((self, other))

    def __radd__(self, other):
        if isinstance(other, str):
            other = self.__class__(null_placeholder, other)
        return StringWithFormatting((other, self))

    def __getattribute__(self, name):
        try:
            return types.MethodType(
                super().__getattribute__('_method_cache')[name], self)
        except KeyError:
            attr = getattr(str, name, None)
            if callable(attr) and not name.startswith('__'):
                @wraps(attr)
                def wrapped_str_method(self, *args, **kwargs):
                    result = attr(self, *args, **kwargs)
                    if isinstance(result, list):
                        result = [
                            self.__class__(self.placeholder, s) for s in
                            result]
                    elif isinstance(result, str):
                        result = self.__class__(self.placeholder, result)
                    return result
                self._method_cache[name] = wrapped_str_method
                return types.MethodType(wrapped_str_method, self)
            else:
                return super().__getattribute__(name)

    def populate(self, terminal, styles):
        return '{}{}{}'.format(
            terminal.normal, self.placeholder.populate(terminal, styles), self)


class StringWithFormatting:
    '''FIXME:
    '''
    __slots__ = ['_content']
    _method_cache = {}

    def __init__(self, content):
        '''FIXME:
        :attr:`_content` is a tuple of string-like objects
        '''
        if isinstance(content, self.__class__):
            self._content = content._content
        elif isinstance(content, StringComponent):
            self._content = (content,)
        elif isinstance(content, str):
            self._content = (StringComponent(null_placeholder, content),)
        else:
            self._content = tuple(content)

    def __repr__(self):
        return '{}({!r})'.format(
            self.__class__.__name__, self._content)

    def __str__(self):
        return ''.join(self._content)

    def __len__(self):
        return sum(map(len, self._content))

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

    def __add__(self, other):
        #FIXME: Tidy this mess up!
        if hasattr(other, '_content'):
            return self.__class__(self._content + other._content)
        elif hasattr(other, 'placeholder'):
            if other.placeholder is self._content[-1].placeholder:
                new_content = self._content[:-1] + (self._content[-1] + other,)
            else:
                new_content = self._content + (other,)
        else:
            if self._content[-1].placeholder is null_placeholder:
                new_content = (
                    self._content[:-1] + (self._content[-1] + StringComponent(
                        null_placeholder, other),))
            else:
                new_content = (
                    self._content +
                    (StringComponent(null_placeholder, other),))
        return self.__class__(new_content)

    def __radd__(self, other):
        # FIXME: Tidy this mess up!
        if hasattr(other, 'placeholder'):
            if other.placeholder is self._content[0].placeholder:
                new_content = (other + self._content[0],) + self._content[1:]
            else:
                new_content = (other,) + self._content
        else:
            if self._content[0].placeholder is null_placeholder:
                new_content = ((
                    StringComponent(null_placeholder, other) +
                    self._content[0],) + self._content[1:])
            else:
                new_content = (
                    (StringComponent(null_placeholder, other),) +
                    self._content)
        return self.__class__(new_content)

    def apply_placeholder(self, placeholder):
        content = [
            StringComponent(c.placeholder + placeholder, c) for c in
            self._content]
        return StringWithFormatting(content)

    def __iter__(self):
        for component in self._content:
            yield from iter(component)

    def _get_slice(self, start, stop):
        slice_start = start if start is not None else 0
        slice_stop = stop if stop is not None else len(self)
        slice_stop = min(slice_stop, len(self))
        result = []
        comp_start = 0
        for component in self._content:
            new_strings = []
            comp_stop = comp_start + len(component)
            if comp_start >= slice_start and comp_stop <= slice_stop:
                result.append(component)
            elif comp_start < slice_start < comp_stop:
                result.append(component[
                    slice_start - comp_start:slice_stop - comp_start])
            elif comp_start < slice_stop <= comp_stop:
                result.append(component[:slice_stop - comp_start])
            comp_start = comp_stop
            if comp_stop >= slice_stop:
                break
        return self.__class__(result)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._get_slice(index.start, index.stop)
        else:
            return str(self)[index]

    def _apply_list_returning_str_method(
            self, name, *args, reference, **kwargs):
        new_components = []
        for component in self._content:
            new_components.extend(getattr(component, name)(*args, **kwargs))
        result = []
        for string in reference:
            component_group = []
            component_group_str = ''
            while True:
                component = new_components.pop(0)
                if component:
                    component_group.append(component)
                    component_group_str += str(component)
                    if component_group_str == string:
                        result.append(self.__class__(component_group))
                        break
        return result

    def __getattr__(self, name):
        '''We attemt to provide access to all methods that are available on a
        regular str object, whilst wrapping up answers appropriately.
        '''
        try:
            return types.MethodType(self._method_cache[name], self)
        except KeyError:
            str_cls_method = getattr(str, name)
            @wraps(str_cls_method)
            def str_method_executor(self, *args, **kwargs):
                reference = str_cls_method(str(self), *args, **kwargs)
                if isinstance(reference, list):
                    return self._apply_list_returning_str_method(
                        name, *args, reference=reference, **kwargs)
                elif isinstance(reference, str):
                    raise NotImplementedError(
                        "str method {!r} has not yet been implemented for a "
                        "{}, sorry :-(".format(name, self.__class__.__name__))
                else:
                    return reference
            self._method_cache[name] = str_method_executor
            return types.MethodType(str_method_executor, self)

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
                    # FIXME: This sort of defeats the point of the regex, as we
                    # only look at whitespace:
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
            first_component = self._content[0]
            last_component = self._content[-1]
            total = (
                (first_component.lstrip(),) +
                self._content[1:-1] +
                (last_component.rstrip(),))
            return self.__class__(total)

    def populate(self, terminal=None, styles=None):
        '''Get the concrete (including terminal escape sequences)
        representation of this string.

        :parameter Terminal terminal: The terminal object to use for turning
            formatting attributes such as :attr:`Root.format.blue` into
            concrete escape sequences.
        :parameter styles: An object from which to look up style definitions,
            which ultimately resolve to escape sequences, but may resolve to
            other intermediaries, including other styles.
        :type styles: StylePlaceholderFactory or dict
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
        return ''.join(
            s.populate(terminal, styles) for s in self._content)
