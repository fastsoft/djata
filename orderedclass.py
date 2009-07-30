# deprecated

"""
Provides classes to permit a class to track the order in which certain
properties and nested classes are declared.  The properties of interest
must inherit ``OrderedProperty`` and assure that their super-class
``__init__``ializers are called.  Classes must inherit ``OrderedClass``.
``(name, value)`` pairs are created by the metaclass of ``OrderedClass``
in lists called ``_properties`` and ``_classes`` for ``OrderedProperty``
and ``OrderedClass`` values in the class and all of its ancestors.
You can create a dictionary from either of these lists to capture a
lookup table of the most recent declarations for each name ::

    >>> class Foo(OrderedClass):
    ...    baz = OrderedProperty()
    ...    bar = OrderedProperty()
    ...    class Baz(OrderedClass): pass
    ...    class Bar(OrderedClass):  pass
    ...

    >>> Foo._properties == [('baz', Foo.baz), ('bar', Foo.bar)]
    True

    >>> Foo._classes == [('Baz', Foo.Baz), ('Bar', Foo.Bar)]
    True

Subclasses inerherit the properties and classes of their parent
classes in reversed method resolution order::


    >>> class Qux(Foo):
    ...     qux = OrderedProperty()
    ...     class Qux(OrderedClass): pass
    ...

    >>> Qux._properties == [
    ...     ('baz', Foo.baz),
    ...     ('bar', Foo.bar),
    ...     ('qux', Qux.qux),
    ... ]
    True

    >>> Qux._classes == [
    ...     ('Baz', Foo.Baz),
    ...     ('Bar', Foo.Bar),
    ...     ('Qux', Qux.Qux),
    ... ]
    True


It's a good practice to filter theses lists for a subclass of
``OrderedClass`` or ``OrderedProperty`` that is of interest for your
particular application since parent classes might be interested in
different properties and classes.  As a reminder, in Python, when
you create a subclass with a metaclass, its metaclass must inherit
the parent class's metaclass and bubble function calls to the 
parent metaclass before running specialized code::

    >>> class QuuxProperty(OrderedProperty):
    ...     def __init__(self, n, *args, **kwargs):
    ...         super(QuuxProperty, self).__init__(*args, **kwargs)
    ...         self.n = n
    ...

    >>> class QuuxMetaclass(OrderedClass.__metaclass__):
    ...     def __init__(self, name, bases, attys):
    ...         super(QuuxMetaclass, self).__init__(name, bases, attys)
    ...         self._quux_properties = [
    ...             (name, property)
    ...             for name, property in self._properties
    ...         ]

    >>> class Quux(OrderedClass):
    ...     __metaclass__ = QuuxMetaclass
    ...     foo = OrderedProperty(1)
    ...

    >>> Quux._quux_properties == [
    ...     ('foo', Quux.foo),
    ... ]
    True


"""

from itertools import count, chain

__all__ = [
    'OrderedProperty',
    'OrderedClass',
    'OrderedMetaclass',
]

# a global counter to measure the monotonic order
# of property declarations.
_next_creation_counter = count().next
# inherits thread safty from the global interpreter lock

class OrderedProperty(object):
    def __init__(self, *args, **kws):
        self._creation_counter = _next_creation_counter()
        # pass the buck:
        super(OrderedProperty, self).__init__(*args, **kws)

class OrderedMetaclass(type):
    def __init__(self, name, bases, attrs):
        super(OrderedMetaclass, self).__init__(name, bases, attrs)
        self._creation_counter = _next_creation_counter()

        # The following code should only run after OrderedClass
        # has been declared.
        try: OrderedClass
        except NameError: return

        for ordered_name, Class in (
            ('_properties', OrderedProperty),
            ('_classes', OrderedMetaclass),
        ):
            setattr(self, ordered_name, sorted(
                (
                    (name, value)
                    for base in reversed(self.__mro__)
                    for name, value in vars(base).items()
                    if isinstance(value, Class)
                ),
                # sorted by their declaration number
                key = lambda (name, value): value._creation_counter
            ))

class OrderedClass(object):
    __metaclass__ = OrderedMetaclass

if __name__ == '__main__':

    import doctest
    doctest.testmod()

