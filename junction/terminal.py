import blessings


class Terminal(blessings.Terminal):
    def draw_block(self, block, x, y):
        for y, line in enumerate(block, start=y):
            self.stream.write(self.move(x, y))
            self.stream.write(line)

_terminal = Terminal()


def get_terminal():
    return _terminal
