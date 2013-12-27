from junction import Root, Label


label = Label(
    'One word in the sentence has ' + Root.format.yellow('special') +
    ' formatting, whilst the rest is determined by whatever is default.')
label.default_format = Root.format.bright_blue
root = Root(label)
root.default_format = Root.format.underline
root.run()
