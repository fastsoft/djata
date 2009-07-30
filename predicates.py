# deprecated

"""\
provides functions for creating Django queries
from predicate data structures.
"""

from django.db.models import Q

def parse(predicate):
    """\
    parses notaion for representing predicates
    as a query value in a URL and produces
    a Django ``Q`` query.
    """

    return P([None, None, [
        sentence.split(u',')
        for sentence in predicate.split(u"/")
    ], u'all'])

def predicate(predicate):
    """\
    constructs a Django ``Q`` query, suitable for
    use as an argument to a queryset's ``filter``
    method from a parsed JSON predicate structure.

    Predicates are recursive lists of strings of this
    form::

        predicate   := [subject, verb, object] |
                       [None, None, [predicate, ...], "any" | "all"] |
                       [None, None, predicate, "not"];
        verb        := "exact" | "iexact" |
                       "startswith" | "istartswith" |
                       "endswith" | "iendswith" |
                       "lt" | "gt" | "lte" | "gte" |
                       "year" | "month" | "day" |
                       "contains" | "icontains" |
                       "range" |
                       "search";

    ``subject`` is a symbol string and the type of ``object``
    depends on the ``verb``.  Most verbs accept strings;
    "in" requires a container (``list``, ``tuple``, etc);
    "range" requires a duple of a start and stop.
    """

    if len(predicate) == 3:
        subject, verb, object = predicate
        assert '__' not in subject, '"Subject names cannot contain "__".'
        return Q(**{
            (u'%s__%s' % (
                 u'__'.join(subject.split(u'.')),
                 verb
            )).encode('utf-8'): object
        })

    elif len(predicate) == 4:
        ignore, ignore, predicates, conjunction = predicate

        if conjunction == 'not':
            assert False, "Predicates do not yet support 'not'."

        return reduce(
            {
                u'all': lambda x, y: x & y,
                u'any': lambda x, y: x | y,
            }[conjunction],
            [
                P(predicate)
                for predicate in predicates
            ]
        )

    else:
        assert False, (
            u"Predicates require three or four terms, not %d." %
            len(predicate)
        )

def P(value):
    """\
    an alias to ``predicate``.
    """

    return predicate(value)

