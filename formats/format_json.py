
from datetime import datetime
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

dumps = wrap(dumps)(complex)

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

class JsonModelFormat(ModelFormat):
    name = 'json'
    content_type = 'application/x-javascript'
    def __call__(self, request, view):

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
            'page_number': context.get('page', None),
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
            return dumps(envelope)
        else:
            return dumps(objects)

class JsonpModelFormat(JsonModelFormat):
    name = 'jsonp'
    def __call__(self, request, view):
        objects = view.get_objects()
        fields = view.get_fields()
        callback = request.JSON.get(
            'callback',
            request.GET.get(
                'callback',
                getattr(
                    self,
                    'callback',
                    getattr(
                        view.meta,
                        'jsonp_callback',
                        getattr(
                            view.meta.model,
                            'jsonp_callback',
                            'callback'
                        )
                    )
                )
            )
        )
        return '%s(%s)' % (
            callback,
            super(JsonpModelFormat, self).__call__(request, view),
        )

