from junction import Root, Fill, Zebra, Terminal

fill1 = Fill()
fill2 = Fill(',')
content = [fill1, fill2] * 10
term = Terminal()
zebra = Zebra(*content, even_format=term.red)
root = Root(zebra)
root.run()
