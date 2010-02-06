
=============================================
Djata REST URL Schema
=============================================
Or: how to build URLs for Djata data services
---------------------------------------------

Djata handles the following URL conventions for HTTP requests that parse and
format both single and multiple object representations.

The view index:

- ``data/``
- ``data.<format>``

All objects from a given table or model:

- ``data/<plural>/``
- ``data/<plural>.<format>``

You can view selected objects in tabular form by providing
an ampersand ``&`` delimited list of record identifiers.

- ``data/<plural>/<id>&``
- ``data/<plural>/<id>&<id>``
- ``data/<plural>/<id>&<id>.<format>``

The ``id`` is a unique index, usually the primary key, but can be overridden by a
view.  See `the view documentation <views.rst>`_ regarding the ``index`` ``Meta``
property for more information.

View a single object for a given identifier:

- ``data/<view>/<pk>/``
- ``data/<view>/<pk>.<format>``

Query String
------------

- ``select=<field>,<field>``: notes which field and in what order they should
  appear as columns in a tabular view.
- ``where=<subject>,<verb>,<object>/<subject>,<verb>,<object>``

Rule grammar::

    rule:
        rule "/" rule
        subject "," verb "," object
    subject:
        name
        name "." name
        # delve into related fields
    verb:  # as in Django filter/exclude verbs
        exact
        iexact
        startswith
        endswith
        istartswith
        iendswith
        lt
        gt
        lte
        gte
        contains
        icontains
        in
        range
        year
        month
        day
        search

- ``order=<field>,<field>``: stable sort order, where the last field mentioned
  is effectively applied last.

Pagination
----------

- ``page_number``
- ``page_length``

JSON Formatting
---------------

Multiple objects in JSON get rendered as an Array of Objects by default.  This
is not always the most compact or useful data representation for consumers like
AJA applications::

    [{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}]

``table`` produces JSON where the respective values of each field appear in the
respective positions of each field::

    [[1, "foo"], [2, "bar"]]

``map`` produces JSON where the outer container is an Object instead of an
Array, where the keys are the primary key of the object and the values are
the object itself::

    {"1": {"id": 1, "name": "foo"}, "2": {"id": 2, "name": "bar"}}

``map`` used in conjunction with ``table`` produces an Object of Arrays::

    {"1": [1, "foo"], "2": [2, "bar"]}

``envelope`` wraps the JSON as would appear above in an "envelope" of
meta-data.  This example incorporates ``envelope``, ``map``, and ``table``
together::

    {
        "field": ["id", "name"],
        "length": 2,
        "page_length": 1,
        "page_number": 1,
        "objects": {
            "1": [1, "foo"],
            "2": [2, "bar"]
        }
    }

At the time of this writing, ``page_length`` and ``page_number`` are broken.

``indent`` enables JSON visual indentation with the given tab stop width.

``allow_nan`` enables the use of ``NaN``, ``Infinity`` and ``-Infinity`` for
the corresponding numeric values instead of ``null``.  These values are beyond
the JSON standard.

``compact`` expresses JSON without spaces after delimiters.

Conf File Formatting
--------------------

- ``key`` the field name to use as the key

- ``value`` the field name to use as the value

Text File Formatting
--------------------

- ``display_header``: either ``yes`` or ``no`` indicating whether to
  show field names in the top row.

- ``capitalize``: if present, indicates that field names should be
  capitalized.

Single Objects
--------------

- ``accept`` provides or overrides an HTTP equivalent Accept header for content
  negotiation (not yet implemented)

- ``ie`` input encoding (not yet implemented)

- ``oe`` output encoding (not yet implemented)

JSON Query
----------

- ``pageLength``: number of objects per page
- ``page``: page number of interest
- ``format``: the file extension of the desired response format
- ``parser``: the file extension of the request post data format
- ``select``: an Array of field names of interest for the response
- ``order``: an Array of field names to sort, from lowest to highest
  precedence.
- ``where``: a rule (possibly compound rules) to filter for the
  interesting objects.

Rule Grammar::

    predicate:
        [subject, verb, object] |
        [subject, "range", [start, stop]] |
        [subject, "in", [...objects]] |
        [null, null, [predicate, ...], "any" | "all"] |
        [null, null, predicate, "not"]

    verb: # correspond directly to Django Query verbs
        "exact" | "iexact" |
        "startswith" | "istartswith" |
        "endswith" | "iendswith" |
        "lt" | "gt" | "lte" | "gte" |
        "year" | "month" | "day" |
        "contains" | "icontains" |
        "search"

HTTP Method
-----------

HTTP Content Negotiation
------------------------

