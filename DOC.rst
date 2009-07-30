

DJATA URL API
=============

requires:

 - django
 - simplejson

optional:
 - pyExcelerator for Excel format


::

    import models
    (r'^data/', include('djata.urls'), {
        'models': models,
    }),

::

    from models import ModelA, ModelB, ModelC
    (r'^data/', include('djata.urls'), {
        'models': (
            ModelA,
            ModelB,
            ModelC,
        ),
    }),

``/data/``:

``/data/.<type>``:

/data/<table>
/data/<table>


Query Parameters

    select=<column>,<column>,<column>

    sort

    group=<column>,<column>

    predicate=sentence*
    
        sentence=<subject>,<verb>,<object>

        <subject> is a <column>

        for data generated from django tables, <verb> is one of
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

    key=<column>
        applicable to .conf files generated from
        multiple records.
        the column name that contains variable names.

    value=<column>
        applicable to .conf files generated from
        multiple records.
        the column name that contains variable values.

    map

    table
        implies "meta"

    id

    meta


JSON Parameters

    all parts are optional
    {'select': [], 'sort': [], 'predicate': [], 'key': '', 'value': ''}

    select Array
        an array of column names

    sort Array
        an array of column names.  column names with a '-' before them
        are sorted in reverse order.

    predicate Array

        [<subject>, <verb>, <object>]
        [null, null, [<predicate>*], "any" | "all"]

        verbs are the same as django

    range Array
        the range of the desired rows for the given query.
        [offset, count] 

    capitalize Boolean
        whether to capitalize the column headings in text format.
    
    display_header Boolean
        relevant to HTML and text.

    type
        the file extension associated with the desired formatting

    accept
        the mime type accociated with the desired formatting,
        corresponding to an HTTP Accept header.
        (not implemented)

    as
        the desired content type, regardless of the actual formatting

    limit
        the maximum number of rows to render

    index
        directs a JSON request to include an index: an array of
        identifiers denoting the order and scope of the selected
        range of rows, whether those rows are provided or not
        (since limit may constrain the size of the response)
        implies "meta"

    meta
        directs a JSON request to return a meta-data container
        that contains the rows of data instead of just
        the rows of data.

