from junction import Label, Stack, Root

label1 = Label('This label is left aligned')
label2 = Label('This label is centred')
label2.halign = 'center'
label3 = Label('This label is right aligned')
label3.halign = 'right'
label4 = Label(
    'This is a really long label, which should hopefully illustrate that a '
    'label is cropped when it hits the edge of the visible screen, even when '
    'its min_height would allow more of it to fit!')
label4.min_height = 2
label5 = Label('See?')
stack = Stack(label1, label2, label3, label4, label5)
root = Root(stack)
root.run()
