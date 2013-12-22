from junction import Root, Text, Zebra, Terminal

text1 = Text('Some interesting text might go here')
text2 = Text('The Zebra will help you differentiate lines')
text3 = Text('A third line will help the logic become clearer')
text3.min_height = 2
content = [text1, text2, text3] * 10
term = Terminal()
zebra = Zebra(*content, odd_format=Root.format.on_color(235))
root = Root(zebra)
root.run()
