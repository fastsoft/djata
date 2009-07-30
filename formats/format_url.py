
from djata.formats import ObjectParser, ObjectFormat
from urllib import urlencode

class UrlencodeFormat(object):
    def coerce(self, field, value):
        if field.null and value == '':
            return None
        if field.blank and value == '':
            return ''
        try:
            return field.to_python(value)
        except:
            raise Exception("Validation error %s to %s" % (repr(value), field.name))

class UrlencodedObjectParser(ObjectParser, UrlencodeFormat):
    name = 'urlencoded'
    content_type = 'application/x-www-urlencoded'

    def __call__(self, request, view):
        fields = view.get_fields()
        return dict(
            (field.attname, self.coerce(field, request.POST[field.attname]))
            for field in fields
            if field.attname in request.POST
        )

class UrlqueryObjectParser(ObjectParser, UrlencodeFormat):
    name = 'urlquery'

    def __call__(self, request, view):
        fields = view.get_fields()
        return dict(
            (field.attname, self.coerce(field, request.GET[field.attname]))
            for field in fields
            if field.name in request.GET
        )

class UrlencodedObjectFormat(ObjectFormat):
    name = 'urlencoded'
    content_type = 'application/x-www-urlencoded'

    def __call__(self, request, view):
        fields = view.get_fields()
        object = view.get_object()
        return urlencode([
            (
                field.attname,
                default_if_none(field.value_from_object(object))
            )
            for field in fields
        ])

def default_if_none(object, default = ''):
    if object is None: return default
    return object

