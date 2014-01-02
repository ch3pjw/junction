Formatting and styles
=====================

One of the goals of Junction is to make handling formatting and styling in
terminal-based applications simpler by working at a higher level than the raw
escape-sequence information provided by librarise like curses and
:mod:`blessings`. However, like all things which work some magic to make life
simpler for you, it can pay to understand a little of how they're put together
so that you can work with them more easily.

Styles vs. formats
^^^^^^^^^^^^^^^^^^

The first concept it's useful to draw out is the distinction in Junction
between a :dfn:`format` and a :dfn:`style`. This is akin to the distinction one
would see in a word processor, where individual formatting notions like 'red',
'bold' or 'underline' can be applied to a portion of text, but styles with
semantic meaning like 'heading', 'paragraph' or 'table' can be defined that
encapsulate those specific formats.

This encapsulation makes maintenance of large documents (or in our case
applications) simpler, because if you want to change what headings look like,
you simply redefine what 'heading' means, rather than doing a painful
find-and-replace operation.

We make this distinction first because throughout this document the word
'format' refers to a specific formatting instruction with a concrete look that
can be applied to your text, whilst the word 'style' refers to a named entity
that can reference any number of formats (or indeed, other styles).


Formatting API
^^^^^^^^^^^^^^

So how does one go about specifying some formatted text using Junction? Let's
look at :file:`examples/quick_brown_fox.py` for a quick overview:

.. literalinclude:: ../../examples/quick_brown_fox.py
   :linenos:
   :lines: 16-
   :emphasize-lines: 22-24


In lines 7-9, we can see some content strings and access to some attributes
with names like 'bold', 'red' and 'underline'. For those of you who are
familiar with :mod:`blessings`, this pattern of attribute access should look
familiar, and the names for the terminal formats are identical. Any format that
can be accessed on a :class:`blessings.Terminal` can be access via
:attr:`jcn.Root.format`. Notice how you construct a formatted string by adding
together blocks of content formatted by the attributes accessed via
:attr:`Root.format` and/or regular strings.

Whilst our behaviour is like :mod:`blessings`', we have some additional
behaviour and restrictions of which you need to be aware:

#. You can only apply formats to strings by calling the format attribute with
   the content that you want to be formatted. Using the format attributes like
   raw escape sequence strings doesn't work in Junction, for reasons that we'll
   come onto later. If you want to apply multiple formats, you should nest your
   calls, like ``Root.format.bold(Root.format.underline('Title'))``.
#. The result of the content concatenation in the example is a special object
   of type :class:`StringWithFormatting`. This object behaves as closely as
   possible to a normal :class:`str`, but preserves the content 'markup' that
   was supplied at creation time.
#. Unlike strings merely containing raw escape sequences,
   :class:`StringWithFormatting` objects are smart when it comes to calculating
   laytout. For example, they can be included inside other objects which have
   redefined what 'normal' formatting means - so whenever your new string would
   revert to the terminal's default format, it instead reverts to whatever it's
   parent wants normal to look like.


Styling API
^^^^^^^^^^^

Styles are built on top of formats. They are similar in how they are inserted
into content strings and how they are drawn to the screen (ultimately the
resolve to a series of terminal escape sequences, just like formats). However,
they provide you with a way to give some semantic meaning to the formatting
that you want to use in your application. Let's look at
:file:`examples/styles.py` for an example:

.. literalinclude:: ../../examples/styles.py
   :linenos:
   :lines: 16-

In lines 4-6 we can see how named styles can be assigned as combinations of
other formats and styles. You can name any style you like by assigning to
:attr:`Root.style.name`. The example shows how it can be useful to make style
heirarchical, so more specific style refer to more general ones. We see that
all 'headings' are underlined, but 'h1' is bold and 'h2' has a specific colour
(dark grey, for those of you taking notes ;-) ).

Styles are used in lines 9-13 in the same way as formats: the are accessed as
attributes, applied by calling them on their content and combined into a
:class:`StringWithFormatting` by addition.


Under the hood
^^^^^^^^^^^^^^

The formatting and styling API of Junction is designed to be reasonably
straight-forward and intuitive, whilst providing intellegence internally when
calculating UI layout. There're quite a few classes involved in the process to
cover a variety of circumstances and help us build our formatting concepts up
logically. This section is presented for any interested parties, but you
shouldn't need to understand it as a regular user.

Placeholders
------------

The most basic building block of our formatting logic is the
:class:`Placeholder`. A :class:`Placeholder` is literally used in a
:class:`StringWithFormatting` in place of a real escape sequence value. This is
important, because our application content can be defined independently of when
it is drawn to the screen. (Imagine the case where someone changes the look of
a 'heading' mid-application.)

We define three different types of :class:`Placeholder`:
:class:`FormatPlaceholer`, :class:`ParameterizingFormatPlaceholder` and
:class:`StylePlaceholder` for referencing formats, formats that take arguments
(such as :attr:`Root.color`) and styles respectively. We also define a fourth
class :class:`PlaceholderGroup`, which acts similarly to :class:`Placholder`,
but is a container for multiple placholders.  :class:`Placholder` objects are
combined by addition to form :class:`PlaceholderGroup` objects.

Instances of :class:`Placholder` are generated for the user by
:class:`FormatPlaceholderFactory` and :class:`StylePlaceholderFactory`, which
are presented to the user as :attr:`Root.format` and :attr:`Root.style`
respectively. In addition to generating :class:`StylePlaceholder` objects, the
:class:`StylePlaceholderFactory` also coordinates registration of user-defined
styles and provides internal access to those definitions when they are needed.
That is, the user can make statements like::

    Root.style.button = Root.format.bold + Root.format.green

for later retrieval.

At draw time, :class:`Placeholders` are replaced with escape squence data
before strings are passed to a :class:`Terminal` for drawing. This process,
which is mirrored by other objects defined in :file:`formatting.py` is
performed by :meth:`Placholder.populate`. Populate requires a :class:`Terminal`
from which to look up terminal escape sequences, and a
:class:`StylePlaceholderFactory` object, which will resolve styles in a similar
manner.

Strings with formatting
-----------------------

Where :class:`Placeholder` objects were the most-basic of our formatting
constructs, at the other end of the level-of-complexity spectrum with have
:class:`StringWithFormatting`. This class endeavours to be everything a string
can be, with the added bonus of being able to attach formatting information to
arbitrary portions of the string. Inevitably this means there is a little bit
of magic going on!

At a fundamental level, :class:`StringWithFormatting` is a simple container for
chunks of string which each have a single format. The
:meth:`StringWithFormatting.populate` method, analgous to
:class:`Placeholder.populate` does this for the entire string. Because a
:class:`StringWithFormatting` is essentially a list of component strings, any
:class:`str` methods which get applied to a :class:`StringWithFormatting` need
to be applied over the whole list of string components, which can complicate
matters somewhat. For example, :meth:`str.stip` should only affect each end of
a :class:`str`, so :class:`StringWithFormatting` has to careful no to apply
:meth:`str.strip` equally every single one of its components.

String components
-----------------

The final class of object that completes the formatting puzzle is the
:class:`StringComponentSpec`. Each :class:`StringComponentSpec` is a
specification of what each portion of a :class:`StringWithFormatting` is like.
It contains some 'content' and refers to a :class:`Placholder` instance for
instruction as to how that content should be formatted.

When populated (via :meth:`StringComponentSpec.populate` in much the same vein
as our other classes), a :class:`StringComponentSpec` returns not only the
escape sequence of its placeholder, but its contents and an escape sequence to
revert the application of its placeholder. Of note is the fact that
:attr:`StringComponentSpec.content` can also be a 'populatable' thing, so
:meth:`StringComponentSpec` will recursively populate it's contents. This means
we need a stack (:class:`EscapeSequenceStack`) to keep track of what escapes
sequences will have been applied in a string so that we can undo them neatly.

:class:`StringComponentSpec` objects are created by the user when they call
:class:`Placeholder` objects with some content. :class:`StringWithFormatting`
objects are then created when :class:`StringComponentSpec` objects are added
together. This makes a nice, seamless API where users don't have to keep track
of all of our internal semantics, whilst giving us severl sensible levels of
abstraction for dealing with the problem, which turns out to be quite
complex(!), of how to draw escape sequences to the screen in a sensible order.
