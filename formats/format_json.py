
# TODO indent
# TODO page_length page_number
# TODO compact
# TODO expand related fields
# TODO use URLs for foreign keys

from datetime import datetime
from django.db.models import ForeignKey
from django.utils.simplejson import *
from djata.python.wrap import wrap
from djata.formats import ModelFormat, ObjectFormat, ModelParser, ObjectParser

def complex(data):
    if data is None:
        return data
    if not isinstance(data, type) and hasattr(data, 'json'):
        return data.json()
    if isinstance(data, list) or isinstance(data, tuple):
        return list(
            complex(datum)
            for datum in data
        )
    elif isinstance(data, dict):
        return dict(
            (complex(key), complex(value))
            for key, value in data.items()
        )
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, int):
        return data
    elif isinstance(data, long):
        return data
    elif isinstance(data, float):
        return data
    elif isinstance(data, basestring):
        return data
    else:
        return unicode(data)

class JsonMixin(object):
    def __call__(self, request, view):

        if 'indent' in request.JSON:
            indent = request.JSON['indent'] or 4
        elif 'indent' in request.GET:
            indent = int(request.GET['indent'] or 4)
        else:
            indent = None

        allow_nan = (
            'allow_nan' in request.GET or
            request.JSON.get('allow_nan', False) == True
        )

        if 'compact' in request.JSON:
            if request.JSON['compact'] == True:
                separators = (',', ':')
        elif 'compact' in request.GET:
            separators = (',', ':')
        else:
            separators = None

        return dumps(
            complex(self.python(request, view)),
            indent = indent,
            allow_nan = allow_nan,
            separators = separators,
        )

class JsonpMixin(object):
    callback = 'callback'
    def __call__(self, request, view):
        callback = request.JSON.get(
            'callback',
            request.GET.get(
                'callback',
                self.callback
            )
        )
        return '%s(%s)' % (
            callback,
            super(JsonpMixin, self).__call__(request, view),
        )

class JsonObjectFormat(JsonMixin, ObjectFormat):
    name = 'json'
    extension = 'json'
    content_type = 'application/x-javascript'

    def cell(self, field, object, view):
        value = field.value_from_object(object)
        if isinstance(field, ForeignKey):
            return {
                field.rel.field_name: object.pk,
                "$type": field.rel.to._meta.verbose_name,
                "$ref": view.get_url_of_object(
                    field.rel.to.objects.get(pk = value)
                ),
            }
        return value

    def python(self, request, view):
        object = view.get_object()
        fields = view.get_fields()
        return dict(
            (field.name, self.cell(field, object, view))
            for field in fields
        )

class JsonpObjectFormat(JsonpMixin, JsonObjectFormat):
    name = 'jsonp'

class JsonObjectParser(ObjectParser):
    extension = 'json'
    content_type = 'application/x-javascript'

    def __call__(self, request, view):
        fields = view.get_fields()
        object = loads(request.raw_post_data)
        return dict(
            (field.attname, object[field.name])
            for field in fields
            if field.name in object
        )

class JsonModelFormat(JsonMixin, ModelFormat):
    name = 'json'
    content_type = 'application/x-javascript'
    def python(self, request, view):

        context = request.context
        objects = view.get_objects()
        fields = view.get_fields()
        field_names = [
            field.name
            for field in fields
        ]

        use_envelope = 'envelope' in request.GET or request.JSON.get('envelope', False)
        use_table = 'table' in request.GET or request.JSON.get('table', False)
        use_map = 'map' in request.GET or request.JSON.get('map', False)
        index = view.index

        envelope = {
            'length': objects.count(),
            'fields': field_names,
            'page_number': context.get('page_number', None),
            'page_length': context.get('page_length', None),
        }

        objects = tuple(dict(
            (field.name, field.value_from_object(object))
            for field in fields
        ) for object in objects)

        if use_table:
            if use_map:
                objects = dict(
                    (object[index.name], tuple(
                        object[field_name]
                        for field_name in field_names
                    ))
                    for object in objects
                )
            else:
                objects = tuple(
                    tuple(
                        object[field_name]
                        for field_name in field_names
                    )
                    for object in objects
                )

        else:
            if use_map:
                objects = dict(
                    (object[index.name], object)
                    for object in objects
                )

        envelope['objects'] = objects

        if use_envelope:
            return envelope
        else:
            return objects

class JsonpModelFormat(JsonpMixin, JsonModelFormat):
    name = 'jsonp'

