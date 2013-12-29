from junction import Root, Text


Root.style.heading = Root.format.underline
Root.style.h1 = Root.style.heading + Root.format.bold
Root.style.h2 = Root.style.heading + Root.format.color(230)

text = Text(
    Root.style.h1('Disclaimer:\n') +
    "This software comes with absolutely no warranty, not even for "
    "merchantability or fitness for a particular purpose\n\n" +
    Root.style.h2('Footnote:\n') +
    "But we've made every effort to make it awesome ;-)")
root = Root(text)
root.run()
