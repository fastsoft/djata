
from urllib2 import urlopen, HTTPError
from urllib import urlencode as urlencode_base, quote
import csv
from itertools import cycle
from cgi import parse_qsl
from urlparse import urljoin
from datetime import datetime
from itertools import count

next_creation_counter = count().next

class MetaModule(object):
    """
        Whenever a ForeignKey(model_name, related_name = None) gets
        declared, a corresponding RelatedField needs to get added to the
        other, related model.  However, at the time of ForeignKey()
        declarations, it isn't even aware of the model with which it is
        associated.  The Model metaclass iterates all of the class
        properties that are Field subtypes and "dubs" them with the property
        name they are given and pairs them with the containing class.
        However, even then, half the time, the related model hasn't been
        declared yet.  So, when a ForeignKey gets "dubbed", it looks "drops
        off" a RelatedField() instance for the related model to "pick up"
        whenever its declared.  The ModelMetaclass keeps a dictionary that
        associates the module object that contains every Model with a
        "MetaModule" instance.  The "MetaModule" is a place where every
        "Model" in a module can "drop off" RelatedField() objects and pick
        them up after they're declared.  The "drop off" method checks to see
        whether the corresponding "related model" has already checked in by
        trying to pick up other related fields.  If the related model has
        already been declared, the drop off method calls the pick up method
        on the model automatically.
    """
    def __init__(self):
        self.models = {}
        # related model name to (field_name, field) list:
        self.store = {}

    # leave a related field for another model
    def dropoff(self, model_name, related_field_name, related_field):
        self.store.setdefault(model_name, list()).append((
            related_field_name,
            related_field
        ))
        if model_name in self.models:
            self.pickup(self.models[model_name])

    # pick up any related fields
    def pickup(self, model):
        self.models[model.__name__] = model
        # pick up related fields
        fields = self.store.get(model.__name__, list())
        for field_name, field in fields:
            field.dub(model, field_name)
            setattr(model, field_name, field)
            model._fields.append(field)
        fields[:] = [] # empty the list

class ModelMetaclass(type):
    """

        The model metaclass ascertains that certain properties of the class
        are declared:

        - objects is an ObjectManger for the model.  It has methods for
          retriving and memoizing instances of objects from the HTTP
          backend.

        - _verbose_name is a dash delimited URL fragment for loading and
          saving an object from the HTTP backend.
        - _verbose_name_plural is a dash delimited URL for loading objects
          in bulk from the HTTP backend.
        - _url is the full URL leading up to but not including an extension
          for loading and saving an object from the HTTP backend.
        - _url_plural is the full URL leading up to but not including the
          extension of multiple objects in the HTTP backend.
        - _creation_counter is a number that is guaranteed to ascend
          monotonically among all model declarations and can be used to sort
          models in declaration order.
        - _index is the name of the key used to construct URL fragments that
          identify individual objects.
        - _module the module object of the containing module.  We use this
          internally to grab the module's "url" property as the base
          URL for generating fully qualified URLs.
        - _meta_module is an object that the metaclasses use to attached
          RelatedField instances to other models, regardless of whether they
          are declared before or after any given model.
        - _fields is a list of field instances including Field(),
          ForeignKey(), and RelatedField() instances in the order that they
          were declared.

    """

    Model = None
    _meta_modules = {}

    def __init__(self, name, bases, attys):
        super(ModelMetaclass, self).__init__(name, bases, attys)

        # ignore the abstract Model
        if self.Model is None:
            self.Model = self
            return

        # discover own module
        self._module = __import__(self.__module__, {}, {}, ['*'])
        # and associate a "meta module" for dropping off and picking
        # up RelatedFields
        if self._module not in self._meta_modules:
            self._meta_modules[self._module] = MetaModule()
        self._meta_module = self._meta_modules[self._module]

        self._creation_counter = next_creation_counter()
        self._fields = list()
        for field_name, value in attys.items():
            if isinstance(value, Field):
                value.dub(self, field_name)
                self._fields.append(value)
        self._fields.sort(key = lambda field: field._creation_counter)

        if '_verbose_name' not in attys:
            self._verbose_name = self.__name__.lower()
        if '_verbose_name_plural' not in attys:
            self._verbose_name_plural = '%ss' % self._verbose_name
        if '_url' not in attys:
            if hasattr(self._module, 'url'):
                self._url = urljoin(self._module.url, self._verbose_name)
        if '_url_plural' not in attys:
            if hasattr(self._module, 'url'):
                self._url_plural = urljoin(self._module.url, self._verbose_name_plural)
        if '_index' not in attys:
            self._index = self._pk

        self.objects = ObjectManager()
        self.objects.dub(self)

        # pick up related fields
        self._meta_module.pickup(self)

class ObjectManager(dict):
    """
        An object manager is a memo of Model instances for a given model,
        mapping from the model's primary key to a model object.  It hosts an
        API for grabbing individual objects and multiple objects.
    """

    def dub(self, model):
        """
            Since it is not possible or desirable to override the
            constructor of a `dict` subtype, the ModelMetaclass for each
            model that is declared calls this method to bind it.
        """
        self.model = model

    def get(self, pk, *args):
        """
            Gets the object for a given primary key.  For example::

                Model.objects.get(pk = 1)

        """
        if not args and pk not in self:
            model = self.model
            object = model()
            object[model._pk] = pk
            object.load()
            model.objects[pk] = object
        return super(ObjectManager, self).get(pk, *args)

    def all(self):
        """
            Downloads and memoizes every instance of the model from the
            backend::

                Model.objects.all()

        """
        reader = csv.DictReader(urlopen(self.model._url_plural + '.csv'))
        return [self.model(**row) for row in reader]

    def filter(self, **where):
        """
            Downloads and memoizes all instances of the model from the
            backend that meet critiera specified as keyword arguments
            mapping a key name to the value it must be equal to::

                Model.objects.filter(other_key = 10)

            Filter is used internally by RelatedFields() to generate lists
            of instances related to a given model by way of a foreign key.
        """
        reader = csv.DictReader(
            urlopen('%s.csv?where=%s' % (
                self.model._url_plural,
                "/".join(
                    "%s,exact,%s" % (key, value)
                    for key, value in where.items()
                )
            ))
        )
        return [self.model(**row) for row in reader]

class Field(property):
    def __init__(self, type = None, blank = None, null = None):
        self.type = type
        self.blank = blank
        self.null = null
        self._creation_counter = next_creation_counter()

    def dub(self, model, name):
        self.model = model
        self.name = name

    def coerce(self, value):
        if self.type is not None:
            value = self.type(value)
        return value

    def __get__(self, instance, klass):
        if instance is None:
            return self
        return self.coerce(instance.get(self.name, None))

    def __set__(self, instance, value):
        instance[self.name] = self.coerce(value)

class ForeignKey(Field):

    def __init__(self, related, related_name = None):
        self.related = related
        self.related_name = related_name
        self._related_model = None
        self._creation_counter = next_creation_counter()

    def dub(self, model, name):
        super(ForeignKey, self).dub(model, name)
        if self.related_name is None:
            self.related_name = model._verbose_name_plural.replace('-', '_')
        model._meta_module.dropoff(
            self.related,
            self.related_name,
            RelatedField(
                model.__name__,
                name,
            )
        )

    @property
    def attname(self):
        related_model = self.related_model
        return related_model.__name__.lower()

    @property
    def related_model(self):
        if self._related_model is None:
            if isinstance(self.related, basestring):
                self._related_model = getattr(self.model._module, self.related)
            else:
                self._related_model = related
        return self._related_model

    def __get__(self, instance, klass):
        if instance is None:
            return self
        return self.related_model.objects.get(
            instance[self.name]
        )

    def __set__(self, instance, value):
        if not isinstance(value, self.related_model):
            value = self.related_model.objects.get(value)
        instance[self.attname] = value.pk

class RelatedField(Field):

    def __init__(self, related, related_name = None):
        self.related = related
        self._related_name = related_name
        self._related_model = None
        self._creation_counter = next_creation_counter()

    def __str__(self):
        return '<RelatedField %s %s>' % (
            self.related,
            self._related_name
        )

    @property
    def related_name(self):
        if self._related_name is None:
            self._related_name = self.model._verbose_name
        return self._related_name

    @property
    def related_model(self):
        if self._related_model is None:
            if isinstance(self.related, basestring):
                self._related_model = getattr(self.model._module, self.related)
            else:
                self._related_model = related
        return self._related_model

    def __get__(self, instance, klass):
        if instance is None:
            return self
        return self.related_model.objects.filter(**{
            self.related_name: instance.pk
        })

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
        raise ApiError('%s\n%s' % (
            (url, argument, object),
            exception.fp.read()
        ))

def models(module):
    return sorted(
        (
            model
            for name, model in vars(module).items()
            if  isinstance(model, type)
                and issubclass(model, Model)
            and model is not Model
        ),
        key = lambda model: model._creation_counter
    )

class MainMetaclass(type):
    """
        When a Main subtype is declared, the Metaclass inspects the name of
        the module in which the Main was declared to determine whether it
        was run as the "main" program.  If so, the MainMetaclass
        instantiates the Main to run a command line interface for the Models
        declared in that module.
    """
    def __init__(self, name, bases, attys):
        super(MainMetaclass, self).__init__(name, bases, attys)
        self.init_module()
        self.init_models()
        if self.__module__ == '__main__':
            import sys
            self(sys)
    def init_module(self):
        self._module = __import__(self.__module__, {}, {}, ())
    def init_models(self):
        self.models = models(self._module)
        self.model_for_view = {}
        for model in self.models:
            self.model_for_view[model._verbose_name] = model
            self.model_for_view[model._verbose_name_plural] = model

class Main(object):
    __metaclass__ = MainMetaclass

    def __init__(self, sys):
        self._sys = sys
        self.command = sys.argv[0]
        if len(sys.argv) == 1:
            self.list_views()
        else:
            view = sys.argv[1]
            self.do(view, *sys.argv[2:])

    def list_views(self):
        print 'Usage: %s VIEW [list|fields|select]'
        print '  Views:'
        for model in self.models:
            print '    %s' % (model._verbose_name_plural,)

    def do(self, view, command = None, *args):
        if command is None:
            command = 'list'
        if view not in self.model_for_view:
            print 'No commands for %r' % view
            self.list_views()
            self._sys.exit(-1)
        model = self.model_for_view[view]
        if not hasattr(self, 'do_%s' % command):
            print 'No such command: %r' % command
        getattr(self, 'do_%s' % command)(model, *args)

    def do_fields(self, model):
        for field in model._fields:
            print field.name.replace('_', '-')

    def do_list(self, model, *args):
        for object in model.objects.all():
            print object[model._pk], object

    def do_select(self, model, *field_names):
        for object in model.objects.all():
            print ", ".join(
                str(reduce(expandattr, field_name.replace('-', '_').split('.'), object))
                for field_name in field_names
            )

def expandattr(object, field_name):
    if isinstance(object, list):
        return [getattr(o, field_name) for o in object]
    else:
        return getattr(object, field_name)

