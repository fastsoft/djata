
Creating Djata Views
====================

Djata views, by default, support a wide variety of formats and
parsers for various `REST schemas <rest.rst>`_ based on the extension
and (in future versions) content negotiation.  These can be
customized.

For example, to create a custom HTML view for multiple foos, using a
template of your own design::

    from djata.formats.format_html import 
    class Foo(View):
        class Meta:
            verbose_name = 'foo'
            verbose_name_plural = 'foos'
        class HtmlModelFormat(HtmlModelFormat):
            template = 'example/foos.html'

The default template for an ``HtmlModelFormat`` is ``djata/model.html``,
but that too can be overridden for all models by providing an
alternate template by the same name earlier in your ``settings.py``
``TEMPLATE_DIRS`` list.

You can also create HTML views that respond to different URLs, like
``fooey.html`` instead of ``foos.html``::

    from djata.formats.format_html import 
    class Foo(View):
        class Meta:
            verbose_name = 'foo'
            verbose_name_plural = 'foos'
        class FooeyHtmlModelFormat(HtmlModelFormat):
            name = 'fooey.html'
            template = 'example/foos.html'

You can also configure many of the defaults for the view by adding
various properties to the ``Meta`` metadata class for your view.

- ``model`` overrides the model that the view is paired to.  By
  default this is inferred from the ``models`` property of the module
  and the name of the view class.
- ``verbose_name`` the name used for single object URLs, that defaults
  to the ``verbose_name`` of the model, which defaults to a lower-
  case version of the class name.
- ``verbose_name_plural`` the name used for multiple object URLs,
  that defaults to the ``verbose_name_plural`` of the model, which in
  turn defaults to a lower-case version of the class name with an
  extra "s".
- ``index`` determines the name of the field that is used in URLs
  to select individual objects.
- ``insecure``, if set to ``True``, permits anyone with access to the
  URL to perform write operations like ``PUT``, ``POST``, and ``DELETE``.
  The intent is to support Django access control in future versions.
- ``default_page_length``, when set to an integer, turns on
  pagination with a particular number of objects per page.
- ``max_page_length`` permits the user to specify any page length on a URL up
  to this value.
- ``default_page_number``, dictates the page that viewers first see.
  The default is ``1``.  ``-1`` shows the last page first.
- ``visible``, if set to ``False``, causes the view to not appear on
  the automatically generated view index.
- ``abstract``, when set to ``True``, tells Djata to ignore the class.
  This is useful for base classes that are not associated with any
  particular model and are not intended to be complete views.
- ``default_format`` is the extension of the format to use for the view by
  default.  If it is not specified, it checks for a variable by the same name
  on the views module.  If neither the class or module specify a format,
  requesting on a URL for the model without providing a format extension will
  result in a "No format specified error".

The ``djata.views.ViewBase`` supports all the features of a ``View``
class but does not support any formats.  This is a good base
class for any view where you want absolute control.

The ``djata.views.View`` base class supports the following formatters
and parsers:

- formats:
-- multiple objects (models):
--- ``.json`` ``formats.format_json.JsonModelFormat``
--- ``.jsonp`` ``formats.format_json.JsonpModelFormat``
--- ``.html`` ``formats.format_html.HtmlModelFormat``
--- ``.basic.html`` ``formats.format_html.HtmlModelFormat``
--- ``.raw.html`` ``formats.format_html.RawHtmlModelFormat``
--- ``.upload.html`` ``formats.format_html.UploadHtmlModelFormat``
--- ``.text`` ``formats.format_text.TextModelFormat``
--- ``.txt`` ``formats.format_text.TextModelFormat``
--- ``.csv`` ``formats.format_csv.CsvModelFormat``
--- ``.xls`` ``formats.format_xls.XlsModelFormat`` (if ``pyExcelerator`` is
--  installed)
-- single objects:
--- ``.html`` ``formats.format_html.HtmlObjectFormat``
--- ``.basic.html`` ``formats.format_html.HtmlObjectFormat``
--- ``.raw.html`` ``formats.format_html.RawHtmlobjectFormat``
--- ``.text`` ``formats.format_text.TextObjectFormat``
--- ``.txt`` ``formats.format_text.TextObjectFormat``
--- ``.urlencoded`` ``formats.format_url.UrlencodedObjectFormat``
- parsers:
-- multiple objects (model):
--- ``.csv`` ``formats.format_csv.CsvModelParser``
-- single objects:
--- ``.urlencoded`` ``formats.format_url.UrlencodedObjectParser``
--- ``.urlquery`` ``formats.format_url.UrlqueryObjectParser``

See `formats <formats.rst>`_ for information on how to create or customize
formatter and parsers classes.

Under the Hood
--------------

When you create a view class, the ViewMetaclass instantiates your
subtype.  In the process, it inspects the class's ``__module__``, the
module name of the module in which the module was declared.  It uses
this to discover or create a ``views`` property on the module object,
an instance of ``djata.views.Views``, which manages URL routing and
indexing for all views.  You can provide an alternate ``views``
instance before your first ``View`` class declaration.

