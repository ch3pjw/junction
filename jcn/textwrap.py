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

from textwrap import TextWrapper as _TextWrapper
from functools import reduce

from .formatting import StringWithFormatting


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
                # FIXME: should this line go? Removing it makes at least simple
                # cases like wrap('    ', 10) actually behave like
                # textwrap.wrap...
                result.append('')
        return result


def wrap(text, width):
    w = TextWrapper(width)
    return w.wrap(text)
