from junction import Root, Text

# The resulting StringWithFormatting passed to the Text element constructor
# below illustrates how we try to match up to blessings' ways of doing
# formatting.
text = Text(
    Root.format.bold('The ') + 'quick ' +
    Root.format.red('brown') + ' fox ' + Root.format.underline('jumps') +
    ' over the lazy dog')
root = Root(text)
root.run()
