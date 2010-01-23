
Formatters
==========

Formatters must support:

- ``name`` is the extension (without the dot prefix) that the class is intended
  to respond to.  There can only be one view class for each extension, but
  multiple subclasses can override different extensions with the same behavior
  or variants thereof.
- ``__call__(request, view)``: must return some kind of
  ``django.http.HttpResponse``.  Accepts the request and a view instance.

The ``view`` object passed to the formatter supports:

- ``get_objects()`` gets all objects that need to be viewed, after accounting
  for ordering, where rule filtering/excluding, pagination, or key selection.
- ``get_fields()`` gets all of the Django fields that need to be viewed, after
  column selection and ordering.

The request has a ``context`` dictionary that develops over the course
of routing and processing and is passed to the template formatter
ultimately.

Template Formatters
-------------------

- ``template``: the name of a Django Template file.
- ``response_class``: some kind of ``django.http.HttpResponse``
- ``process(request, view)`` may alter ``request.context`` for the template.

HTML formatters are template formatters.

