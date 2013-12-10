from junction import Root, Text, Zebra, Terminal

text1 = Text('Some interesting text might go here')
text2 = Text('The Zebra will help you differentiate lines')
content = [text1, text2] * 10
term = Terminal()
zebra = Zebra(*content, odd_format=term.on_color(235))
root = Root(zebra)
root.run()
