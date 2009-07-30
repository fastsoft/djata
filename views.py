# deprecated

from types import ModuleType

from django.db.models import *
from django.http import HttpResponse

import djata.predicates as predicates
from djata.middleware import JsonRequestMiddleware
from djata.python.names import lower

from django.utils import simplejson

import djata.formatters
table_formatters = vars(djata.formatters)

default_limit = 50

def decorator(function1):
    def decorator2(*args1, **kws1):
        def decorator3(function):
            def decorator4(*args2, **kws2):
                args = args1 + args2
                kws1.update(kws2)
                return function1(function, *args, **kws1)
            decorator4.func_name = function.func_name
            return decorator4
        return decorator3
    decorator2.func_name = function1.func_name
    return decorator2

@decorator
def models_view(function, request, *args, **kws):
    models = kws['models']
    if isinstance(models, dict):
        pass
    elif isinstance(models, ModuleType):
        models = dict(
            (lower(name, '-'), model)
            for name, model in vars(models).items()
            if isinstance(model, type)
            and Model in model.__mro__
            and model != Model
        )
    elif isinstance(models, list) or isinstance(models, tuple):
        models = dict(
            (lower(model._meta.object_name, '-'), model)
            for model in models
        )
    else:
        assert False, 'No models supplied to the data app'
    kws['models'] = models
    request.models = models
    return function(request, *args, **kws)

def model_view(function):
    @models_view()
    def decorated(request, *args, **kws):

        model_name = kws['model_name']
        del kws['model_name']

        models = kws['models']

        del kws['models']
        model = kws['model'] = models[model_name]

        request.model = model
        request.column_names = list(
            field.name
            for field in model._meta.fields
        )

        return function(request, *args, **kws)
    return decorated

def selectable(function):
    def decorated(request, *args, **kws):

        select = None
        if 'select' in request.JSON:
            select = request.JSON['select']
        if 'select' in request.GET:
            select = request.GET['select'].split(',')

        if select is not None:
            request.column_names = list(
                column_name
                for column_name in select
                if column_name in request.column_names
            )

        return function(request, *args, **kws)

    return decorated

def table_view(default_type_name = 'json'):
    def decorator(function):
        def decorated(request, *args, **kws):

            capitalize = False
            if 'capitalize' in request.GET:
                capitalize = request.GET['capitalize']
                if capitalize == '':
                    capitalize = True
                else:
                    capitalize = simplejson.loads(capitalize)
            if 'capitalize' in request.JSON:
                capitalize = request.JSON['capitalize']
            request.capitalize = capitalize

            type_name = kws.get('type_name', None)
            if type_name is None:
                type_name = default_type_name
            del kws['type_name']
            if 'type' in request.GET:
                type_name = request.GET['type']
            if 'type' in request.JSON:
                type_name = request.JSON['type']

            sort = []
            if 'sort' in request.JSON:
                sort.extend(request.JSON['sort'])
            if 'sort' in request.GET:
                sort.extend(request.GET['sort'].split(','))

            predicate = None
            if 'predicate' in request.JSON:
                predicate = predicates.P(request.JSON['predicate'])
            if 'predicate' in request.GET:
                predicate = predicates.parse(request.GET['predicate'])

            display_header = True
            if 'display_header' in request.JSON:
                display_header = request.JSON['display_header']
            if 'display_header' in request.GET:
                display_header = simplejson.loads(request.GET['display_header'])
            request.display_header = display_header

            request.limit = None
            if 'limit' in request.GET:
                request.limit = int(request.GET['limit'])
            if 'limit' in request.JSON:
                request.limit = request.JSON['limit']
                assert isinstance(request.limit, int)

            if not hasattr(request, 'user') or not request.user.is_active:
                if request.limit is None:
                    request.limit = default_limit
                request.limit = min(request.limit, default_limit)

            rows = function(request, *args, **kws)

            if hasattr(request, 'column_names'):
                column_names = request.column_names
            else:
                column_names = set(
                    column_name
                    for row in rows
                    for column_name in row.keys()
                )

            if isinstance(rows, type) and Model in rows.__mro__:

                rows = rows.objects.all()

                if predicate:
                    rows = rows.filter(predicate)

                if sort:
                    rows = rows.order_by(*sort)

                rows = list(
                    Adapter(row)
                    for row in rows
                )

            if request.limit is not None:
                rows = rows[:request.limit]

            content_type, content = table_formatters[type_name](
                request,
                rows,
            )

            if 'as' in request.GET:
                content_type = str(request.GET['as'])
            if 'as' in request.JSON:
                content_type = request.JSON['as'].encode('utf-8')

            return HttpResponse(
                content,
                mimetype = content_type
            )

        return decorated
    return decorator

@JsonRequestMiddleware
@models_view()
@table_view('html')
def models(request, models):
    request.column_names = ['model']
    return list(
        dict(model = model)
        for name, model in models.items()
    )

@JsonRequestMiddleware
@model_view
@table_view('json')
@selectable
def model(request, model):

    schema = False
    if 'schema' in request.JSON:
        schema = bool(request.JSON['schema'])
    if 'schema' in request.GET:
        if request.GET['schema'] == '':
            schema = True
        else:
            schema = simplejson.loads(request.GET['schema'])
            assert isinstance(schema, bool)

    if schema:
        request.column_names = ['name', 'type']
        return list(
            dict(
                name = field.name,
                type = field.__class__.__name__,
            )
            for field in model._meta.fields
        )

    else:
        return model

@JsonRequestMiddleware
@model_view
@table_view('json')
@selectable
def records(request, pks, model):
    return list(
        Adapter(record)
        for record in model.objects.filter(
            pk__in = list(
                int(pk)
                for pk in pks.split('&')
                if pk != ''
            )
        )
    )

@JsonRequestMiddleware
@model_view
@table_view('json')
@selectable
def record(request, pk, model, type_name = None):
    request.column_names = ['key', 'value']
    record = model.objects.get(pk = int(pk))
    return list(
        {
            'key': key,
            'value': value,
        }
        for key, value in vars(record).items()
    )

class Adapter(object):
    def __init__(self, object):
        self.object = object
    def __getitem__(self, key):
        return getattr(self.object, key)

class MetaView(type):
    def __init__(self, name, bases, attys):
        self._meta = self.Meta()
        super(MetaView, self).__init__(name, base, attys)

class View(HttpResponse):
    __metaclass__ = MetaView

    def __init__(self, *args, **kws):
        content, content_type = x, x
        super(View, self).__init__(content, mimetype = content_type)

    def auth(self):
        return True

    class Meta:
        pass

    """
    urlpatterns = patterns('',
        (r'^(?:/|\.(?P<type_name>.*))?$', 'djata.views.model'),
        (r'^/(?P<id>[^/&\.]+)(?:\.(?P<type_name>.*))?$', 'djata.views.record'),
        (r'^/(?P<ids>(?:[^/&\.]&?)+)(?:\.(?P<type_name>.*))?$', 'djata.views.records'),
    )
    """

class OpenView(View):

    filters = ()
    formatters = ()

    def items(self):
        pass

    def filter(self):
        pass

    def format(self):
        pass

    def auth(self):
        return True

class MetaView(object):
    def __new__(self, name, bases, attys):
        return type(name, bases, attys)

class View(HttpResponse):
    __metaclass__ = MetaView
    def __init__(self, request, *args, **kws):
        content, content_type = self.process_request(request, *args, **kws)
        super(View, self).__init__(content, content_type)

