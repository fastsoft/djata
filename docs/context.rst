
Djata Template Context Generation
=================================

The following describe the top-level variables Djata provides for the execution
context for a template.  These can be used in any Djata template-based view,
like anything that mixes in ``djata.formats.TemplateFormat``, such as any of the
formatters exported by ``djata.formats.format_html``.  These include:

- ``RawHtmlFormat`` (defaults to the ``.raw.html`` extension)
- ``HtmlFormat`` (defaults to the ``.html`` extension)

Any View
--------

- ``request``: the Django HTTP ``Request`` object.
- ``settings``: the Django settings module.
- ``url``: an object representing the current URL, that can be used
  to render the current URL, or variations of that URL with
  slightly different query strings.

Single Object Page
------------------

- ``object``

The object will also be aliased with a variable by the same name as
the view.

Raw HTML Model Format
---------------------

- ``fields``
- ``table``
- ``field_names``

Multiple Object Page
--------------------

- ``objects``
- ``filters``

The objects will also be aliased with a variable by the same name as
the view.

Index Page
----------

- ``views`` an array of view metadata objects, each constructed from
  ``view.Meta`` for each view in the relevant views module.

Pagination
----------

- ``page_number`` the current page number
- ``page_length`` the number of objects per page
- ``paginator`` the ``django.core.paginator.Paginator`` object
- ``page`` the ``django.core.paginator.Page`` object
- ``fixed_page_length`` is boolean and indicates that the paginator is
  in use.
- ``page_groups`` is a list of lists.  The inner lists are guaranteed
  to include the first, current, and last page number.  The lists
  also include page numbers from the current page number's
  "neighborhood" at various orders of magnitude.


UserError
---------

You can subclass ``djata.exceptions.UserError`` to create custom error pages for
user exceptions.  If you create a ``UserError`` subclass called ``FoobarError``, by
default the exception will be rendered with the
``djata/errors/foobar_error.html`` template and the HTTP response object will be
``HttpResponseBadRequest``.  These can be overridden with the ``template`` and
``response_class`` properties.

In the template context, you can expect the following variables:

- ``title``: the error title, like "Foobar error"
- ``error``: the exception object

If you do not provide a template for your error, Djata will render the generic
``djata/errors/base.html`` template.

