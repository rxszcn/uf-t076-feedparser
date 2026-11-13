.. _reference.entry.authors:

``entries[i].authors``
============================

A list of authors of this entry.

.. seealso::

    * :ref:`reference.entry.author`
    * :ref:`reference.entry.author_detail`

If the same author is declared more than once -- for example by both
``dc:creator`` and an Atom ``author`` element, or by repeated ``author``
elements -- the declarations are merged into a single list entry. Identity is
judged from the first field that both declarations provide, in this order:

1.  the email address,
2.  the author's URL,
3.  the author's name.

Email addresses are compared case-insensitively, URLs case-sensitively, and
names case-insensitively. An email address is the strongest signal because it
identifies a single mailbox, so two declarations that both provide one are
considered different authors when the addresses differ, even if the names
match. A URL is a stable profile identifier but can be shared by a group, and a
name is the weakest signal because it is frequently duplicated. Declarations
that share no populated field are kept as separate authors.

Blank fields are dropped, so an author that declares an empty name and an email
address appears as ``{'email': '...'}`` rather than ``{'name': '', ...}``.

.. rubric:: Comes from

* /atom10:feed/atom10:entry/atom10:author
* /atom03:feed/atom03:entry/atom03:author
* /rss/channel/item/dc:creator
* /rss/channel/item/dc:author
* /rss/channel/item/itunes:author
* /rdf:RDF/rdf:item/dc:creator
* /rdf:RDF/rdf:item/dc:author
