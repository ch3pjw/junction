from junction import Terminal, Root, Text

term = Terminal()
text = Text(
    term.bold + 'The ' + term.normal + 'quick ' + term.red('brown') + ' fox ' +
    term.underline('jumps') +
    ' over {t.green_on_white}the lazy{t.normal} dog'.format(t=term))
root = Root(text)
root.run()
