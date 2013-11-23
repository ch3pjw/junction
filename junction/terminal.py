import blessings

from .formatting import Format, StringWithFormatting


class Terminal(blessings.Terminal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._normal = super()._resolve_formatter('normal')
        # Because we override blessings.Terminal's formatter lookup to return
        # our own Format objects, we have to make the stream smart about
        # converting them for writing. (Deriving format str would have played
        # badly with blessing's own str-derived objects.)
        orig_stream_write = self.stream.write
        def format_aware_stream_write(data):
            if isinstance(data, Format):
                orig_stream_write(str(data))
            else:
                orig_stream_write(data)
        self.stream.write = format_aware_stream_write

    def draw_block(self, block, x, y, normal=None):
        for y, line in enumerate(block, start=y):
            self.stream.write(self.move(y, x))
            if isinstance(line, StringWithFormatting):
                line = line.draw(normal or self._normal)
            self.stream.write(line)

    def _resolve_formatter(self, name):
        if name == 'normal':
            resolved = None
        else:
            resolved = super()._resolve_formatter(name)
        return Format(resolved, name=name)

_terminal = Terminal()


def get_terminal():
    return _terminal
