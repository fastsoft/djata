
Djata
=====

Djata is a Django application plugin that provides REST services for
existing Django models with minimal but flexible configuration.
Configuring a Djata REST API is comparable to configuring Django's
administrative interface.

Djata views support HTTP GET, PUT, PUSH, and DELETE, with parsers
and formatters including but not limited to HTML, raw HTML for AJAX,
JSON, JSONP, URL encoding, CSV, formatted plain text, and XLS (with
the ``pyExcellerator`` module installed), with orthogonal support
for selecting, filtering, ordering, and paginating data.  Djata
becomes your new base-line for Django views, with support across
the board for the comprehensive API options you want but never
have time to write.

(If you are viewing this page on Github, you will need to visit the `canonical
location of this file <djata/blob/master/README.rst>`_ for the relative
hyperlinks to function properly.)

- `Quick Start Guide <docs/quick-start.rst>`_
- `Configuring Djata URLs <docs/urls.rst>`_
- `Configuring and Creating Views <docs/views.rst>`_
- `REST Schema <docs/rest.rst>`_
- `Template Contexts <docs/context.rst>`_
- `Overriding Existing Templates <docs/templates.rst>`_
- `Configuring and Creating Formatters and Parsers <docs/formats.rst>`_
- `Roles of JSON in Djata <docs/json.rst>`_
- `Client-side API Models <docs/api.rst>`_
- `Installation Notes <docs/install.rst>`_
- `Configuring Django Settings <docs/settings.rst>`_

For an example Djata application, check see 
`Bugwar <http://github.com/fastsoft/bugwar>`_.

In future versions, Djata should support:

- Django authentication for write, delete, and most importantly read
  privileges first for models and then for individual objects.
- HTTP content negotiation on URLs that do not provide a format
  extension.
- A progressively enhanced, cross-referenced, HTML user interface. 
- Custom views for viewing and editing charts, graphs, and trees.
- Throttling and Pacing

