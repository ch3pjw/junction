from junction import Root, Text

# The resulting StringWithFormatting passed to the Text element constructor
# below illustrates how we try to match up to blessings' ways of doing
# formatting. Note that we can't currently insert well into strings with
# .format()!
text = Text(
    Root.format.bold + 'The ' + Root.format.normal + 'quick ' +
    Root.format.red('brown') + ' fox ' + Root.format.underline('jumps') +
    ' over {r.format.green_on_white}the lazy{r.format.normal} dog'.format(
        r=Root))
root = Root(text)
root.run()
