Fixed
-----

*   Aggregate author fields consistently. Blank author fields are dropped, so
    an author with an empty name falls back to its email address (or URL) in
    ``author``, ``author_detail``, and ``authors`` alike. Declarations that
    describe the same author -- including ``dc:creator`` combined with an Atom
    ``author`` element -- are merged into one ``authors`` entry, using the
    email address, then the URL, then the name as identity fields in that
    order. Contributor lists are deduplicated the same way.
