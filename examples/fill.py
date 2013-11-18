from junction import Terminal, Fill

terminal = Terminal()

fill = Fill()
fill.terminal = terminal
with terminal.fullscreen():
    fill.draw(width=terminal.width, height=terminal.height)
    input()
