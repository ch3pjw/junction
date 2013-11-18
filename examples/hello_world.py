from junction import Terminal, Text

terminal = Terminal()

text = Text('Hello world')
text.terminal = terminal
with terminal.fullscreen():
    text.draw(width=6, height=terminal.height)
    input()
