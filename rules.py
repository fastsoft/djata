"""\
provides functions for creating Django queries
from predicate data structures.
"""

from django.db.models import Q

def parse_rules(*rules):
    """\
    parses notaion for representing sentential filter rules
    as a query value in a URL and produces
    a Django ``Q`` query.
    """

    return R([None, None, [
        rule.split(u',')
        for rule in rules
    ], u'all'])

def R(rule):
    """\
    constructs a Django ``Q`` query, suitable for
    use as an argument to a queryset's ``filter``
    method from a parsed JSON predicate structure.

    Rules are recursive lists of strings of this
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

    if len(rule) == 3:
        subject, verb, object = rule
        assert '__' not in subject, '"Subject names cannot contain "__".'
        return Q(**{
            (u'%s__%s' % (
                 u'__'.join(subject.split(u'.')),
                 verb
            )).encode('utf-8'): object
        })

    elif len(rule) == 4:
        dontcare, dontcare, rules, conjunction = rule

        if conjunction == 'not':
            assert False, "Rules do not yet support 'not'."

        return reduce(
            {
                u'all': lambda x, y: x & y,
                u'any': lambda x, y: x | y,
            }[conjunction],
            [
                R(rule)
                for rule in rules
            ]
        )

    else:
        assert False, (
            u"Rules require three or four terms, not %d." %
            len(rule)
        )

