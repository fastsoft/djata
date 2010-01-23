
Djata HTML views use the ``djata/style.html`` and its parent
``djata/base.html`` views for all rendering.  These templates can be
intercepted and overridden by providing templates by those names in
a ``TEMPLATE_DIR`` that appears earlier in your project's
``settings.py``.

Djata uses the ``djata/base.html`` template for all rendering.  Other
templates fill in the ``title``, ``content``, and ``head`` blocks.

See `template contexts <contexts.rst>`_ for information on what
variables are provided to template contexts, how to use templates
with custom views, and how to create custom views for errors.

