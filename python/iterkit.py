"""\
Provides tools for working with iterations, including enumerations,
boolean and transitive comparisons, and others.

Provides "any" and "all" functions for determining whether
any or all of an iteration of boolean values are true.  Provides
an enumerate function for pairing the items of an iteration
with the index of their occurence.  Provides transitive functions
for evaluating where every adjacent pair in an iteration passes
a given test, specifically all comparison relationships like
equality, inequality, less than, less than or equal to by their
two letter names: eq, ne, lt, le, gt, and ge respectively.  On that
topic, also provides |respective|, a function that returns an
iteration of tuples of the respective elements of multiple iterations.
"""

from itertools import *
from wrap import wrap
from types import GeneratorType

try:
    all = all
except NameError:
    def all(items):
        for item in items:
            if not item:
                return False
        return True

try:
    any = any
except:
    def any(items):
        for item in items:
            if item:
                return True
        return False

def transitive(function):
    def transitive(items): 
        items = iter(items)
        try:
            prev = items.next()
            while True:
                next = items.next()
                if not function(prev, next):
                    return False
            prev = next
        except StopIteration:
            pass
        return True 
    return transitive

eq = transitive(lambda x, y: x == y)
ne = transitive(lambda x, y: x != y)
lt = transitive(lambda x, y: x < y)
le = transitive(lambda x, y: x <= y)
gt = transitive(lambda x, y: x > y)
ge = transitive(lambda x, y: x >= y)

try:
    reversed = reversed
except NameError:
    def reversed(items):
        return iter(tuple(items)[::-1])

def shuffle(items, buffer = None):
    raise Exception("Not implemented.")
    if buffer is not None:
        pass
    else:
        pass

def group(predicate, items):
    raise Exception("Not implemented.")

# Apparently, enumerate is part of the builtin library now.
# Part of me is glad someone else thought the exact same
# thing would be a good idea.
enumerate = enumerate

#def enumerate(items):
#    return respective(count(), items)

respective = zip

@wrap(list)
def flatten(elements):
    for element in elements:
        if any(
            isinstance(element, klass)
            for klass in (list, tuple, GeneratorType)
        ):
            for child in flatten(element):
                yield child
        else:
            yield element

def first(elements):
    elements = iter(elements)
    return elements.next()

if __name__ == '__main__':
    assert all(int(a) == b for a, b in respective(['0', '1', '2'], range(10)))
    assert all(eq([a, b, c]) for a, (b, c) in enumerate(enumerate(range(10))))
    assert all(lt([a, b]) for a, b in enumerate(n + 1 for n in range(10)))

