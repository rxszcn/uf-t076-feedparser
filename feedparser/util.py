# Copyright 2010-2025 Kurt McKee <contactme@kurtmckee.org>
# Copyright 2002-2008 Mark Pilgrim
# All rights reserved.
#
# This file is a part of feedparser.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import re
import warnings

# This matches an email address, possibly followed by a ``?subject=`` query.
email_pattern = re.compile(
    r"(([a-zA-Z0-9_.+-]+)@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)"
    r"|(([a-zA-Z0-9-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(]?))"
    r"(\?subject=\S+)?"
)

# The fields that make up a single author. All three are optional, but at least
# one of them must be present for an author declaration to be meaningful.
AUTHOR_FIELDS = ("name", "email", "href")

# Identity is judged from the strongest shared field. Email addresses identify
# a mailbox and are globally unique; profile URLs are stable but may be shared;
# names are the weakest signal because they are frequently duplicated.
AUTHOR_IDENTITY_PRIORITY = ("email", "href", "name")


def clean_author_record(record):
    """Remove blank author fields in place.

    An empty ``<name/>`` must not leave a ``'name': ''`` key behind: the
    single-value author would fall back to the email address while the
    ``authors`` list would still advertise a blank name.
    """

    for field in AUTHOR_FIELDS:
        if field not in record:
            continue
        value = record[field]
        if isinstance(value, str):
            value = value.strip()
        if value:
            record[field] = value
        else:
            del record[field]


def _identity_value(field, value):
    value = value.strip()
    # Email addresses are case-insensitive; names are compared case-insensitively
    # because feeds freely vary capitalization. URLs stay case-sensitive.
    if field in ("email", "name"):
        return value.casefold()
    return value


def authors_share_identity(left, right):
    """Return whether two author records describe the same person.

    The highest-priority field that *both* records provide decides identity.
    If both provide an email address, only the email address is compared; if
    only one provides an email address, the next field both provide is used.
    Records with no overlapping populated field cannot be proven to match.
    """

    for field in AUTHOR_IDENTITY_PRIORITY:
        left_value = left.get(field)
        right_value = right.get(field)
        if left_value and right_value:
            return _identity_value(field, left_value) == _identity_value(
                field, right_value
            )
    return False


def aggregate_authors(records):
    """Deduplicate author records by identity, preserving declaration order.

    Records are expected to be already cleaned. When a record duplicates an
    earlier one, it takes the earlier one's position and fills in any fields
    the earlier record supplied. Later declarations win on conflicting values,
    so the last declaration remains the authoritative one.
    """

    authors = []
    for record in records:
        matches = []
        # Merging fills fields, which can reveal further overlap, so repeat
        # until the identity closure has been resolved.
        while True:
            found = False
            for index, existing in enumerate(authors):
                if index in matches:
                    continue
                if authors_share_identity(existing, record):
                    matches.append(index)
                    for field in AUTHOR_FIELDS:
                        if not record.get(field) and existing.get(field):
                            record[field] = existing[field]
                    found = True
            if not found:
                break

        if not matches:
            authors.append(record)
            continue

        first = min(matches)
        for index in sorted(matches, reverse=True):
            if index != first:
                del authors[index]
        authors[first] = record

    return authors


def render_author(record):
    """Render a single author record using the shared fallback order.

    The fallback order (name, then email, then URL) is used by both the
    single-value ``author`` field and the entries of the ``authors`` list.
    """

    name = record.get("name")
    email = record.get("email")
    href = record.get("href")
    if name and email:
        return f"{name} ({email})"
    if name:
        return name
    if email:
        return email
    if href:
        return href
    return None


def split_author_text(value):
    """Split a free-form author string into a ``(name, email)`` pair.

    RSS feeds carry the author as plain text, often in the forms
    ``"me@example.com (Example editor)"`` or ``"Example editor (me@example.com)"``.
    """

    author = value.strip()
    email = None
    emailmatch = email_pattern.search(author)
    if emailmatch:
        email = emailmatch.group(0)
        # Probably a better way to do the following, but it passes all the tests.
        author = author.replace(email, "")
        author = author.replace("()", "")
        author = author.replace("<>", "")
        author = author.replace("&lt;&gt;", "")
        author = author.strip()
        if author and (author[0] == "("):
            author = author[1:]
        if author and (author[-1] == ")"):
            author = author[:-1]
        author = author.strip()
    return (author or None), email


class FeedParserDict(dict):
    keymap = {
        "channel": "feed",
        "items": "entries",
        "guid": "id",
        "date": "updated",
        "date_parsed": "updated_parsed",
        "description": ["summary", "subtitle"],
        "description_detail": ["summary_detail", "subtitle_detail"],
        "url": ["href"],
        "modified": "updated",
        "modified_parsed": "updated_parsed",
        "issued": "published",
        "issued_parsed": "published_parsed",
        "copyright": "rights",
        "copyright_detail": "rights_detail",
        "tagline": "subtitle",
        "tagline_detail": "subtitle_detail",
    }

    def __getitem__(self, key, _stacklevel=2):
        """
        :return: A :class:`FeedParserDict`.
        """

        if key == "category":
            try:
                return dict.__getitem__(self, "tags")[0]["term"]
            except IndexError:
                raise KeyError("object doesn't have key 'category'")
        elif key == "enclosures":
            return [
                FeedParserDict(
                    [(name, value) for (name, value) in link.items() if name != "rel"]
                )
                for link in dict.__getitem__(self, "links")
                if link["rel"] == "enclosure"
            ]
        elif key == "license":
            for link in dict.__getitem__(self, "links"):
                if link["rel"] == "license" and "href" in link:
                    return link["href"]
        elif key == "updated":
            # Temporarily help developers out by keeping the old
            # broken behavior that was reported in issue 310.
            # This fix was proposed in issue 328.
            if not dict.__contains__(self, "updated") and dict.__contains__(
                self, "published"
            ):
                warnings.warn(
                    "To avoid breaking existing software while "
                    "fixing issue 310, a temporary mapping has been created "
                    "from `updated` to `published` if `updated` doesn't "
                    "exist. This fallback will be removed in a future version "
                    "of feedparser.",
                    DeprecationWarning,
                    stacklevel=_stacklevel,
                )
                return dict.__getitem__(self, "published")
            return dict.__getitem__(self, "updated")
        elif key == "updated_parsed":
            if not dict.__contains__(self, "updated_parsed") and dict.__contains__(
                self, "published_parsed"
            ):
                warnings.warn(
                    "To avoid breaking existing software while "
                    "fixing issue 310, a temporary mapping has been created "
                    "from `updated_parsed` to `published_parsed` if "
                    "`updated_parsed` doesn't exist. This fallback will be "
                    "removed in a future version of feedparser.",
                    DeprecationWarning,
                    stacklevel=_stacklevel,
                )
                return dict.__getitem__(self, "published_parsed")
            return dict.__getitem__(self, "updated_parsed")
        else:
            realkey = self.keymap.get(key, key)
            if isinstance(realkey, list):
                for k in realkey:
                    if dict.__contains__(self, k):
                        return dict.__getitem__(self, k)
            elif dict.__contains__(self, realkey):
                return dict.__getitem__(self, realkey)
        return dict.__getitem__(self, key)

    def __contains__(self, key):
        if key in ("updated", "updated_parsed"):
            # Temporarily help developers out by keeping the old
            # broken behavior that was reported in issue 310.
            # This fix was proposed in issue 328.
            return dict.__contains__(self, key)
        try:
            self.__getitem__(key, _stacklevel=3)
        except KeyError:
            return False
        return True

    has_key = __contains__

    def get(self, key, default=None):
        """
        :return: A :class:`FeedParserDict`.
        """

        try:
            return self.__getitem__(key, _stacklevel=3)
        except KeyError:
            return default

    def __setitem__(self, key, value):
        key = self.keymap.get(key, key)
        if isinstance(key, list):
            key = key[0]
        return dict.__setitem__(self, key, value)

    def __getattr__(self, key):
        # __getattribute__() is called first; this will be called
        # only if an attribute was not already found
        try:
            return self.__getitem__(key, _stacklevel=3)
        except KeyError:
            raise AttributeError("object has no attribute '%s'" % key)

    def __hash__(self):
        # This is incorrect behavior -- dictionaries shouldn't be hashable.
        # Note to self: remove this behavior in the future.
        return id(self)
