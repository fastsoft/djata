
- ``DJATA_MEDIA_URL`` is necessary for use of the ``djata/style.html`` but not
  necessary if ``djata/style.html`` or ``djata/base.html`` are overridden.
- ``TEMPLATE_DIRS``: the path, ``join(dirname(djata.__file__), 'templates')``,
  needs to appear somewhere, preferably after any Djata applications that might
  want to override the default.s

