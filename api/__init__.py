
from urllib2 import urlopen, HTTPError
from urllib import urlencode as urlencode_base, quote
from cgi import parse_qsl
from urlparse import urljoin
from datetime import datetime

class ModelMetaclass(type):
    def __init__(self, name, bases, attys):
        super(ModelMetaclass, self).__init__(name, bases, attys)
        for field_name, value in attys.items():
            if isinstance(value, Field):
                value.dub(self, field_name)
        self.module = __import__(self.__module__, {}, {}, ['*'])
        if '_verbose_name' not in attys:
            self._verbose_name = self.__name__.lower()
        if '_url' not in attys:
            if hasattr(self.module, 'url'):
                self._url = urljoin(self.module.url, self._verbose_name)
        if '_index' not in attys:
            self._index = self._pk
        self.objects = ObjectManager()
        self.objects.dub(self)

class ObjectManager(dict):
    def dub(self, model):
        self.model = model
    def get(self, key, *args):
        if not args and key not in self:
            model = self.model
            object = model()
            object[model._pk] = key
            object.load()
            model.objects[key] = object
        return super(ObjectManager, self).get(key, *args)

class Field(property):
    def __init__(self, type = None, blank = None, null = None):
        self.type = type
        self.blank = blank
        self.null = null
    def dub(self, model, name):
        self.model = model
        self.name = name
    def coerce(self, value):
        if self.type is not None:
            value = self.type(value)
        return value
    def __get__(self, instance, klass):
        return self.coerce(instance.get(self.name, None))
    def __set__(self, instance, value):
        instance[self.name] = self.coerce(value)

class ForeignKey(Field):

    def __init__(self, rel):
        self.rel = rel
        self._foreign_model = None

    def dub(self, model, name):
        self.model = model
        self.name = name

    @property
    def attname(self):
        foreign_model = self.foreign_model
        return '%s_%s' % (
            foreign_model.__name__.lower(),
            foreign_model._pk
        )

    @property
    def foreign_model(self):
        if self._foreign_model is None:
            if isinstance(self.rel, basestring):
                self._foreign_model = getattr(self.model.module, self.rel)
            else:
                self._foreign_model = rel
        return self._foreign_model

    def __get__(self, instance, klass):
        return self.foreign_model.objects.get(instance[self.attname])

    def __set__(self, instance, value):
        if not isinstance(value, self.foreign_model):
            value = self.foreign_model.objects.get(value)
        instance[self.attname] = value.pk

class Model(dict):
    __metaclass__ = ModelMetaclass

    _pk = 'id'

    @property
    def pk(self):
        return self.get(self._pk, None)

    def save(self):
        self.update(urlopenapi(
            (
                self._index not in self and
                '%s/' % self._url or
                '%s/%s' % (self._url, quote(str(self[self._index])))
            ),
            {
                'action': (
                    self.pk is None
                    and 'add' or 'change'
                ),
                'format': 'urlencoded',
                'parser': 'urlencoded',
            },
            self
        ))
        self.objects[self.pk] = self
        return self

    def load(self):
        pk = self.pk
        if pk not in self.objects:
            self.update(
                urlopenapi('%s/%s.urlencoded' % (
                    self._url,
                    quote(str(self[self._index]))
                ))
            )
            self.objects[pk] = self
        return self.objects[pk]

    def __unicode__(self):
        return u'%s' % self[self._index]

    def __repr__(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            self.pk
        )

class ApiError(Exception):
    pass

def urldecode(string):
    return dict(parse_qsl(string))

def urlencode(items):
    def coerce(value):
        if value is None:
            return ''
        if isinstance(value, datetime):
            return value.isoformat(' ')[:19]
        return value
    if isinstance(items, dict):
        items = items.items()
    return urlencode_base([
        (key, coerce(value))
        for key, value in items
    ])

def urlopenapi(url, argument = None, object = None):
    try:
        if argument is None:
            argument = {}
        if object is None:
            return urldecode(urlopen(url + '?' + urlencode(argument)).read())
        else:
            argument = urlencode(argument)
            object = urlencode(object)
            result = urldecode(
                urlopen(url + '?' + argument, object).read()
            )
            return result
    except HTTPError, exception:
        import traceback
        raise ApiError(exception.fp.read())

