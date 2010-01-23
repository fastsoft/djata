
Initial Setup
=============

Consider a Django app that has the following models:

``example/models.py``::

    import django.db.models as models

    class Foo(models.Model):
        label = models.CharField(max_length = 20)

    class Bar(models.Model):
        foo = models.ForeignKey('Foo')

Then in a views file, you would configure the models you would like to make
visible.  You will need to export a "models" variable, presumably your models
module.  Then, for each model you would like to appear, create a class by the
same name that inherits from ``djata.views.View``.  See `the views
documentation <views.rst>`_ for more information on customizing views.

``example/views.py``::

    from djata.views import *
    import example.models as models

    class Foo(View):
        class Meta:
            verbose_name = 'foo'
            verbose_name_plural = 'foos'

    class Bar(View):
        class Meta:
            verbose_name = 'bar'
            verbose_name_plural = 'bars'

At the time of this writing, recent versions of Django expose the model's
``verbose_name`` and ``verbose_name_plural`` (that Django uses for URLs of
single and multiple objects) as some kind of proxy object that is not
inspectable without an instance, so these need to be manually overridden in the
class's ``Meta`` metadata class.

You would configure URL patterns to use Djata with your Djata views.  See `the
URL's documentation <urls.rst>`_ for more information about configuring URL
patterns.

``example/urls.py``::

    from django.conf.urls.defaults import *

    urlpatterns = patterns('',
        (r'^data(?=\.|/)', include('djata.urls'), {
            'module_name': 'example.views',
        }),
    )

