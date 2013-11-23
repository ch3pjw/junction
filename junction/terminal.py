import blessings

from .formatting import Format, StringWithFormatting


class Terminal(blessings.Terminal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._normal = super()._resolve_formatter('normal')

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
