
Adding a Djata Application to URL Patterns
==========================================

Turning your document root over to Djata::

    (r'^', include('djata.urls_root'), {
        'module_name': 'myapp.views',
    }),

Djata uses the name "root" to mean that it is responsible for all content that
follows a slash, which is implicit in the first ``urls.py`` in a request route.
Turning everything following a slash ``/`` over to Djata is similar::

    (r'^data/', include('djata.urls_root'), {
        'module_name': 'myapp.views',
    }),

However, if you give Djata a URL that has already processed through a URL like
"data" but you let Djata discover whether the name is followed by a file
extension or a slash, it can use the file extension to infer the GET or POST
format::

    # XXX discouraged usage, read on
    (r'^data', include('djata.urls'), {
        'module_name': 'myapp.views',
    }),

It is best to use a lookahead expression to ascertain that only ``data/*`` and
``data.*`` catch your URL, but not something like ``data-sources``::

    (r'^data(?=\.|/)', include('djata.urls'), {
        'module_name': 'myapp.views',
    }),
    (r'^data-sources/$', 'myapp.views.data_sources'),

You can similarly create a URL pattern for a single model, either for single or
multiple objects::

    # squirrel table
    (r'squirrels/', include('data.urls_model_root'), {
        'module_name': 'myapp.views',
        'view_name': 'squirrel',
    }),
    (r'squirrels(?=\.|/)', include('data.urls_model'), {
        'module_name': 'myapp.views',
        'view_name': 'squirrel',
    }),
    # single squirrel pages
    (r'squirrel/', include('data.urls_model_root'), {
        'module_name': 'myapp.views',
        'view_name': 'squirrel',
    }),
    (r'squirrel(?=\.|/)', include('data.urls_model'), {
        'module_name': 'myapp.views',
        'view_name': 'squirrel',
    }),

You can supply any of these options in the keyword dictionary, or create named
capture groups in your URL patterns:

- ``module_name`` the name of a Djata views module
- ``view_name`` the verbose name of a Djata view, either singular or
  plural, from the corresponding view's ``Meta.verbose_name`` or
  ``Meta.verbose_name_plural``, which are automatically extracted from the
  respective values from the underlying Model, but may be overridden either on
  the Model or the View [1]_.
- ``model``
- ``pk`` the primary key of a single object
- ``pks`` the primary keys of some objects
- ``format`` the extension corresponding to either the format of the
  desired GET response or the format of a POST request.  If no format is
  supplied to the view, it uses either a reasonable default or content
  negotiation [2]_.


.. [1] at the time of this writing, ``verbose_name`` and
   ``verbose_name_plural`` have to be set manually since recent Django builds
   use proxy objects for those purposes, and cannot be inspected for their
   string value.

.. [2] content negotiation is not implemented at the time of this writing.

