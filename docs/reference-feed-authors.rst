.. _reference.feed.authors:

``feed.authors``
============================

A list of authors of this feed.

The list is aggregated with the same rules as :ref:`reference.entry.authors`:
blank fields are dropped, declarations that describe the same author are
merged, and identity is judged from the email address, then the URL, then the
name.
