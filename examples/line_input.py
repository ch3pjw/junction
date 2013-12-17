from junction import LineInput, Root, Terminal

terminal = Terminal()
line_input = LineInput(terminal.color(240)('This is some placeholder text'))
root = Root(line_input)
root.run()
