
The Djata Client API
====================

The ``djata/api`` directory can be checked out anywhere and provides Python
base-classes like the Django database ORM (``django.db.models``) that can be used
to create simple client-side API's for any objects hosted on a URL by Djata.
The client-side API will uses plain URL encoded data and python's ``urllib`` to
HTTP GET, PUT, POST, and DELETE records mediated by a Djata service.

Considering, the `example <quick-start.rst>`_ application, the client-side API
could look like::

    from djata.api import Model, Field

    url = "http://example.com/data"

    class Foo(Model):
        id = Field()
        label = Field()

    class Bar(Model):
        id = Field()
        foo = ForeignKey('Foo')

    if __name__ == '__main__':

        foo = Foo()
        foo.label = 'Pitty da foo'
        foo.save()
        id = foo.id

        bar = Bar()
        bar.foo = foo
        bar.save()

        foo = Foo.objects.get(id)
        foo.load()

