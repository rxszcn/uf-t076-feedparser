.. _reference.entry.author:

``entries[i].author``
============================

The author of this entry.

This is the final author declaration in :ref:`reference.entry.authors`, rendered
from a single set of fallback rules: the name, then the email address, then the
author's URL. A name and an email address are combined as
``"name (email@example.com)"``. Blank values are ignored, so an author that
declares an empty name and an email address is reported as the email address in
both this field and the ``authors`` list.

.. seealso::

    * :ref:`reference.entry.author_detail`
    * :ref:`reference.entry.authors`

.. rubric:: Comes from

* /atom10:feed/atom10:entry/atom10:author
* /atom03:feed/atom03:entry/atom03:author
* /rss/channel/item/dc:creator
* /rss/channel/item/dc:author
* /rss/channel/itunes:author
* /rdf:RDF/rdf:item/dc:creator
* /rdf:RDF/rdf:item/dc:author
