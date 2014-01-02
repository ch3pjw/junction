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


class EscapeSequenceStack:
    def __init__(self, default_escape_sequence):
        self.default_escape_sequence = default_escape_sequence
        self._stack = []

    def push(self, esc_seq):
        self._stack.append(esc_seq)

    def pop(self):
        '''Pops the last escape sequence from the stack *and returns a string
        containing all the remaining escape sequences that should be in effect
        on the terminal*.
        '''
        self._stack.pop()
        return self.default_escape_sequence + ''.join(self._stack)


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
            raise TypeError(
                "Can't add object of type {} to {!r} - to construct content "
                "using formatting placeholders, please call the placeholder "
                "with the content you desire to be formatted".format(
                    type(other), self))

    def __call__(self, content):
        return StringComponentSpec(self, content)

    def populate(self, terminal, styles):
        raise NotImplementedError()


class FormatPlaceholder(Placeholder):
    def populate(self, terminal, styles):
        return getattr(terminal, self.attr_name)


class ParameterizingFormatPlaceholder(FormatPlaceholder):
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
        if not self.args:
            self.args = args
            return self
        else:
            return super().__call__(*args)

    def populate(self, terminal, styles):
        self._protect_from_not_called()
        return super().populate(terminal, styles)(*self.args)


class StylePlaceholder(Placeholder):
    def populate(self, terminal, styles):
        style = styles[self.attr_name]
        return style.populate(terminal, styles)


class PlaceholderGroup:
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


class FormatPlaceholderFactory:
    '''FIXME: document this
    '''
    __slots__ = []  # Ensure noone can store arbitrary attributes on us

    def __getattr__(self, attr_name):
        if attr_name == '__isabstractmethod__':
            return False
        else:
            if attr_name in ('color', 'on_color'):
                return ParameterizingFormatPlaceholder(attr_name)
            else:
                return FormatPlaceholder(attr_name)


class StylePlaceholderFactory:
    __slots__ = ['_defined_styles']

    def __init__(self):
        super().__setattr__('_defined_styles', {})

    def __getattr__(self, name):
        if name == '__isabstractmethod__':
            return False
        else:
            return StylePlaceholder(name)

    def __setattr__(self, name, value):
        if value is None:
            del self._defined_styles[name]
        else:
            self._defined_styles[name] = value

    def __getitem__(self, name):
        return self._defined_styles[name]


class StringComponentSpec:
    '''A string component specification is an object that will be used to form
    part of a string-like object that contains formatting information as well
    as printable characters.
    '''
    __slots__ = ['placeholder', 'content']

    def __init__(self, placeholder, content):
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
        if hasattr(self.content, 'chunk'):
            chunks = self.content.chunk(regex)
        else:
            chunks = regex.split(self.content)
        chunks = [self.__class__(self.placeholder, c) for c in chunks if c]
        return chunks

    def populate(self, terminal, styles, esc_seq_stack):
        esc_seq = self.placeholder.populate(terminal, styles)
        esc_seq_stack.push(esc_seq)
        if hasattr(self.content, 'populate'):
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
        if spec1 and spec2 and spec1.placeholder == spec2.placeholder:
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

    def __getattr__(self, name):
        '''We attemt to provide access to all methods that are available on a
        regular str object, whilst wrapping up answers appropriately.
        '''
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

    def _apply_str_method(self, method_name, *args, reference, **kwargs):
        '''Applies the named method of str to self by calling it on each of our
        component specs and aggregating the return values correctly.

        :parameter method_name: the name of the (*list-returning*) str method
            to call
        :parameter reference: a reference result (i.e. the result of the method
            call on a normal string) so that we can fix any breaks in our
            return values caused by boundaries between formats, rather than the
            called method.
        '''
        strings_with_formatting = []
        for spec in self._content:
            specs = getattr(spec, method_name)(*args, **kwargs)
            strings_with_formatting.extend(map(self.__class__, specs))
        result = []
        for str_unit in reference:
            if str_unit:
                formatted_unit = strings_with_formatting.pop(0)
                while True:
                    if str(formatted_unit) == str_unit:
                        result.append(formatted_unit)
                        break
                    formatted_unit += strings_with_formatting.pop(0)
        return result

    def chunk(self, regex):
        reference = regex.split(str(self))
        return self._apply_str_method('chunk', regex, reference=reference)

    def strip(self):
        if len(self._content) == 0:
            return self
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
